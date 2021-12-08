function select_copy(text) {
    let textarea = document.getElementById('message_block_textarea');
    textarea.innerText = text;
    textarea.select();
    document.execCommand('copy');
}

function messageShow(text = null) {
    let message = document.getElementById('message_block');
    if (message.classList.contains('show') && !message.classList.contains('is-loading')) {
        return null
    }
    if (text !== null) {
        message.classList.remove('is-loading');
        message.children[0].innerText = text;
    } else {
        message.classList.add('is-loading');
        message.classList.add('show');
    }
}

function messageHidden() {
    let message = document.getElementById('message_block');
    message.children[0].innerText = '';
    message.classList.remove('show');
}

function get_url(cid) {
    return `http://170.130.40.103/api/v1/place/${cid}/html`
    // return `http://127.0.0.1:8000/api/v1/place/${cid}/html`
}

async function copy_place_data(cid) {
    let text;
    messageShow();
    await fetch(get_url(cid), {mode: "no-cors"}).then(
        async response => {
            if (response.status === 200) {
                text = 'Copied'
            } else {
                text = 'Error'
            }
            messageShow(text);
            setTimeout(function () {
                messageHidden();
            }, 1000);

            let html = response.text()
            select_copy(await html)
            return html
        }
    ).catch(error => console.log(error))
}

function closeModal() {
    let modal = document.getElementById('modal');
    modal.classList.toggle('is-active');
}

function open_preview(cid) {
    let url = get_url(cid);
    let modal = document.getElementById('modal');
    modal.classList.toggle('is-active');
    let iframe = document.getElementById('place_iframe');
    iframe.setAttribute('src', url)
}

async function preview_place_data(cid) {
    open_preview(cid)
}


let place_copy_buttons = document.querySelectorAll('i.clone_icon');
console.log(place_copy_buttons)
place_copy_buttons.forEach(item => {
    item.addEventListener('click', function () {
        copy_place_data(this.dataset.placeCid)
    })
})


let place_open_buttons = document.querySelectorAll('i.expand_icon');
console.log(place_open_buttons)
place_open_buttons.forEach(item => {
    item.addEventListener('click', function () {
        preview_place_data(this.dataset.placeCid)
    })
})