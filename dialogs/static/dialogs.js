/**
 * Web-components base class.
 */
class HTMLElementDialogs extends HTMLElement {

    static _observed = ['project', 'api'];

    constructor() {
        super();
        this.shadow = this.attachShadow({ mode: "open" });
        // // FIXME: Icons don't work https://stackoverflow.com/a/66693250
        // this.shadow.innerHTML = `
        //     <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH" crossorigin="anonymous">
        //     <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css" rel="stylesheet">`;
        this._dom = {}
    }

    connectedCallback() {
        this._setup();
    }

    static get observedAttributes() {
        return this._observed;
    }

    attributeChangedCallback(name, oldValue, newValue) {
        if (oldValue !== newValue) {
            this[name] = newValue;
        }
    }
}


class HTMLElementDialogsActivity extends HTMLElementDialogs {

    static _observed = [...this._observed, 'maxlines'];

    _setup() {
        this.shadowRoot.innerHTML += `
            No activity found
        `;
        let url = `${this.api}/project/${encodeURIComponent(this.project)}/log`;
        url += (this.maxlines !== undefined) ? `/${this.maxlines}` : '';
        const source = new EventSource(url);
        source.addEventListener('open', event => {
            this.shadowRoot.innerHTML = '';
        });
        source.addEventListener('message', event => {
            if (this.shadowRoot.innerHTML) {
                this.shadowRoot.appendChild(document.createElement('br'));
            }
            this.shadowRoot.appendChild(document.createTextNode(event.data));
            if (this.maxlines !== undefined) {
                // Calculate the total number of lines (each line has a <br> element after it)
                const totalLines = Math.ceil(this.shadowRoot.childNodes.length / 2);
                // Remove nodes to display the number of lines specified by maxlines
                while (this.shadowRoot.childNodes.length > this.maxlines*2) {
                    if (this.shadowRoot.firstChild.nodeType === Node.TEXT_NODE) {
                        this.shadowRoot.removeChild(this.shadowRoot.firstChild); // Remove text node
                    }
                    if (this.shadowRoot.firstChild.nodeType === Node.ELEMENT_NODE && this.shadowRoot.firstChild.tagName === 'BR') {
                        this.shadowRoot.removeChild(this.shadowRoot.firstChild); // Remove <br> element
                    }
                }
            }
            // TODO: Add fire event 'message' to allow user to eg. scroll to bottom
        });
        source.addEventListener('error', event => {
            // TODO: Add fire event 'error' containing `event.data` to allow user to eg. display alert
            this.shadowRoot.innerHTML = `
                <i class="bi bi-bug-fill me-2"></i>
                <strong>Error:</strong> ${event.data || 'Could not load activity'}
            `;
            console.error("Could not load activity", event);
            source.close();
        });
    }
}
customElements.define("dialogs-activity", HTMLElementDialogsActivity);
