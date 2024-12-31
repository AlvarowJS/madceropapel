// "use strict";
var KTCardDraggable;

KTGenerarDraggable();

function KTGenerarDraggable() {
    let containers = document.querySelectorAll('.draggable-zone');
    if (containers.length > 0) {
        KTCardDraggable = new Sortable.default(containers, {
            draggable: '.draggable',
            handle: '.draggable .draggable-handle',
            mirror: {
                //appendTo: selector,
                appendTo: 'body',
                constrainDimensions: true
            }
        });
    }
}