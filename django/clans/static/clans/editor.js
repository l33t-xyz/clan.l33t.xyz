document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('editor-form');
    if (!form) return;
    const field = document.getElementById('id_html'),
        status = document.getElementById('save-state'),
        title = document.getElementById('id_title');
    const q = new Quill('#rich-editor', {
        theme: 'snow',
        placeholder: 'Every story starts somewhere…',
        modules: {
            toolbar: [
                [{ header: [2, 3, false] }],
                ['bold', 'italic', 'underline', 'strike'],
                [{ list: 'ordered' }, { list: 'bullet' }],
                ['blockquote', 'link'],
                ['clean'],
            ],
        },
        formats: [
            'header',
            'bold',
            'italic',
            'underline',
            'strike',
            'list',
            'blockquote',
            'link',
            'image',
        ],
    });
    q.clipboard.dangerouslyPasteHTML(field.value);
    q.root.setAttribute('aria-label', 'Page content');
    const labels = {
        bold: 'Bold',
        italic: 'Italic',
        underline: 'Underline',
        strike: 'Strikethrough',
        blockquote: 'Quote',
        link: 'Insert link',
        clean: 'Clear formatting',
        list: 'List',
    };
    document.querySelectorAll('.ql-toolbar button').forEach((b) => {
        for (const [key, label] of Object.entries(labels)) {
            if (b.classList.contains('ql-' + key)) {
                b.setAttribute(
                    'aria-label',
                    key === 'list'
                        ? b.value === 'ordered'
                            ? 'Numbered list'
                            : 'Bullet list'
                        : label
                );
                b.title = b.getAttribute('aria-label');
            }
        }
    });
    document
        .querySelectorAll('.ql-picker-label')
        .forEach((e) => e.setAttribute('aria-label', 'Text heading style'));
    let dirty = false,
        saving = false;
    function changed() {
        dirty = true;
        status.textContent = 'Unsaved changes';
        const b = document.getElementById('publish-button');
        if (b) {
            b.disabled = true;
            b.title = 'Save your draft before publishing';
        }
    }
    q.on('text-change', (_, __, source) => {
        if (source === 'user') changed();
    });
    title.addEventListener('input', changed);
    form.addEventListener('submit', () => {
        field.value = q.getSemanticHTML();
        saving = true;
    });
    window.addEventListener('beforeunload', (e) => {
        if (dirty && !saving) {
            e.preventDefault();
            e.returnValue = '';
        }
    });
    function insert(url) {
        const range = q.getSelection(true);
        q.insertEmbed(
            range ? range.index : q.getLength() - 1,
            'image',
            url,
            'user'
        );
    }
    document
        .querySelectorAll('[data-insert-image]')
        .forEach((b) =>
            b.addEventListener('click', () => insert(b.dataset.insertImage))
        );
    document
        .getElementById('image-upload')
        .addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (!file) return;
            const note = document.getElementById('upload-status');
            note.textContent = 'Adding your image…';
            const data = new FormData();
            data.append('image', file);
            try {
                const res = await fetch(form.dataset.upload, {
                    method: 'POST',
                    body: data,
                    headers: {
                        'X-CSRFToken': form.querySelector(
                            '[name="csrfmiddlewaretoken"]'
                        ).value,
                    },
                });
                const result = await res.json();
                if (!res.ok)
                    throw Error(result.error || "Image couldn't be added.");
                insert(result.url);
                note.textContent =
                    'Image added. Save your draft to keep it on this page.';
            } catch (err) {
                note.textContent = err.message;
            } finally {
                e.target.value = '';
            }
        });
});
