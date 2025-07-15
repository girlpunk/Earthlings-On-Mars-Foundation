from django import forms

class LuaEditor(forms.Textarea):
    def __init__(self, *args, **kwargs):
        super(LuaEditor, self).__init__(*args, **kwargs)
        self.attrs['class'] = 'lua-editor'
        self.attrs['style'] = 'width: 90%; height: 100%;'

    class Media:
        css = {
            'all': (
                'https://cdnjs.cloudflare.com/ajax/libs/codemirror/6.65.7/codemirror.min.css',
            )
        }
        js = (
            'https://cdnjs.cloudflare.com/ajax/libs/codemirror/6.65.7/codemirror.min.js',
            'https://cdnjs.cloudflare.com/ajax/libs/codemirror/6.65.7/mode/lua/lua.min.js',
            '/static/codemirror-6.65/init.js'
        )

