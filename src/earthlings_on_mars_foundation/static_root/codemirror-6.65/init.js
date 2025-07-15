
(function(){
    var $ = django.jQuery;
    $(document).ready(function(){
        $('textarea.lua-editor').each(function(idx, el){
            CodeMirror.fromTextArea(el, {
                lineNumbers: true,
                mode: 'lua'
            });
        });
    });
})();

