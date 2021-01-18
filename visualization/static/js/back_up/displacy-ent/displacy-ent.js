//- ----------------------------------
//- 💥 DISPLACY ENT
//- ----------------------------------

'use strict';

class displaCyENT {
    constructor (api, options) {
        this.api = api;
        this.container = document.querySelector(options.container || '#displacy');

        this.defaultText = options.defaultText || null;
        this.defaultModel = options.defaultModel || null;
        this.defaultEnts = options.defaultEnts || null;

        this.onStart = options.onStart || false;
        this.onSuccess = options.onSuccess || false;
        this.onError = options.onError || false;
        this.onRender = options.onRender || false;

    }

    parse(text = this.defaultText, model = this.defaultModel, ents = this.defaultEnts) {
        if(typeof this.onStart === 'function') this.onStart();

        let xhr = new XMLHttpRequest();
        xhr.open('POST', this.api, true);
        xhr.setRequestHeader('Content-type', 'text/plain');
        xhr.onreadystatechange = () => {
            if(xhr.readyState === 4 && xhr.status === 200) {
                if(typeof this.onSuccess === 'function') this.onSuccess();
                this.render(text, JSON.parse(xhr.responseText), ents);
            }

            else if(xhr.status !== 200) {
                if(typeof this.onError === 'function') this.onError(xhr.statusText);
            }
        }

        xhr.onerror = () => {
            xhr.abort();
            if(typeof this.onError === 'function') this.onError();
        }

        xhr.send(JSON.stringify({ text, model }));
    }

    render(text, spans, ents,title) {
        //this.container.innerHTML = '';
        let offset = 0;

        const Title=document.createElement('h1')
        Title.innerHTML = title
        this.container.appendChild(Title);
        var ascii=/[^\u0000-\u007F]/;
        var index=0;


        spans.forEach(({ type, start, end,label }) => {
                   
                   if ( text.slice(offset, start).match(ascii))  {
                    var len=text.slice(offset, start).match(ascii).length
                var num=0
                console.log(text.slice(offset, start))
               
                spans.slice(index).forEach(({ type, start, end,label }) =>{

                    spans.slice(index)[num]['start']=start-len;
                    spans.slice(index)[num]['end']=end-len;
                    num++
                     

                })
            
                start=start-len;
                end=end-len
               
            }



            const fragments = text.slice(offset, start).split('\n');
            fragments.forEach((fragment, i) => {
                
                this.container.appendChild(document.createTextNode(fragment));
                if(fragments.length > 1 && i != fragments.length - 1) this.container.appendChild(document.createElement('br'));
            });
      
       

         const entity_pre = text.slice(start, end);
         if (entity_pre.match(ascii)){
            len=entity_pre.match(ascii).length
            end=end+2*len
            var num=0;
            spans.slice(index+1).forEach(({ type, start, end,label }) =>{

                    spans.slice(index+1)[num]['start']=start-len;
                    spans.slice(index+1)[num]['end']=end-len;
                    num++;

                })


         }
         const entity=text.slice(start, end);
    

            if(ents.includes(type.toLowerCase())) {
                const mark = document.createElement('mark');
                mark.setAttribute('data-entity', type.toLowerCase());
                mark.setAttribute('label', label);
                mark.appendChild(document.createTextNode(entity));
                this.container.appendChild(mark);
            }

            else {
                this.container.appendChild(document.createTextNode(entity));
            }

            offset = end;
            index++;
        

        });

        this.container.appendChild(document.createTextNode(text.slice(offset, text.length)));

        //console.log(`%c  HTML markup\n%c<div class="entities">${this.container.innerHTML}</div>`, 'font: bold 16px/2 arial, sans-serif', 'font: 13px/1.5 Consolas, "Andale Mono", Menlo, Monaco, Courier, monospace');

        if(typeof this.onRender === 'function') this.onRender();
    }
}

