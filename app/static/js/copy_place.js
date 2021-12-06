function select_copy(elem) {
    text = document.getElementById(copy_id);
    var input = document.createElement('input');
    input.setAttribute('value', text.innerHTML);
    document.body.appendChild(input);
    input.select();
    var result = document.execCommand('copy');
    document.body.removeChild(input);
    success = document.getElementById('copy_success');
    success.style = 'display:block;';
    setTimeout(function () {
        success.style = 'display:none;'
    }, 500);
}

