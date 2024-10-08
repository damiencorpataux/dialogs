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

    static _observed = [...this._observed, 'maxlines', 'reverse'];

    _setup() {
        this.shadowRoot.innerHTML += `No activity found`;
        let url = `${this.api}/project/${encodeURIComponent(this.project)}/log`;
        url += (this.maxlines !== undefined) ? `/${this.maxlines}` : '';
        const source = new EventSource(url);
        window.addEventListener('beforeunload', event => {
            source.close();
        });
        source.addEventListener('open', event => {
            this.shadowRoot.innerHTML = '';
        });
        let loaded = false;
        source.addEventListener('message', event => {
            const isReverse = this.hasAttribute('reverse');
            // Add new line
            // const line = document.createTextNode(event.data);
            const line = document.createElement('div');
            line.innerText = event.data;
            line.part = 'line';
            if (isReverse) {
                if (this.shadowRoot.innerHTML) {
                }
                this.shadowRoot.prepend(line);
            } else {
                if (this.shadowRoot.innerHTML) {
                }
                this.shadowRoot.append(line);
            }
            // Remove lines to display the number of lines specified by maxlines
            if (this.maxlines !== undefined) {
                while (this.shadowRoot.childNodes.length > this.maxlines * 2) {
                    if (isReverse) {
                        if (this.shadowRoot.lastChild.nodeType === Node.TEXT_NODE) {
                            this.shadowRoot.removeChild(this.shadowRoot.lastChild); // Remove text node
                        }
                        if (this.shadowRoot.lastChild.nodeType === Node.ELEMENT_NODE && this.shadowRoot.lastChild.tagName === 'BR') {
                            this.shadowRoot.removeChild(this.shadowRoot.lastChild); // Remove <br> element
                        }
                    } else {
                        if (this.shadowRoot.firstChild.nodeType === Node.TEXT_NODE) {
                            this.shadowRoot.removeChild(this.shadowRoot.firstChild); // Remove text node
                        }
                        if (this.shadowRoot.firstChild.nodeType === Node.ELEMENT_NODE && this.shadowRoot.firstChild.tagName === 'BR') {
                            this.shadowRoot.removeChild(this.shadowRoot.firstChild); // Remove <br> element
                        }
                    }
                }
            }
            if (!loaded) {
                this.dispatchEvent(new Event('loaded'));  // Fire once after first message received
                loaded = true;
            }
        });
        source.addEventListener('error', event => {
            // TODO: Add fire event 'error' containing `event.data` to allow user to eg. display alert
            this.shadowRoot.innerHTML = `<strong>Error:</strong> ${event.data || 'Could not load activity'}`;
            console.error("Could not load activity", event);
            source.close();
        });
    }
}
customElements.define("dialogs-activity", HTMLElementDialogsActivity);
