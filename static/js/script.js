window.onload = function () {
    var today = new Date();
    today.setDate(today.getDate() + 1);
    var expirationDate = new Date();
    expirationDate.setDate(today.getDate() + 29);

    var expirationDateString = expirationDate.toISOString().split('T')[0];

    document.getElementById("expiration_date").value = expirationDateString;

    var todayString = today.toISOString().split('T')[0];
    var maxDateString = expirationDate.toISOString().split('T')[0];

    document.getElementById("expiration_date").setAttribute("min", todayString);
    document.getElementById("expiration_date").setAttribute("max", maxDateString);
};

// https://quilljs.com/docs/modules/toolbar
var quill = new Quill('#editor', {
    theme: 'snow',
    modules: {
      toolbar: [
        [{ header: [1, 2, 3, false] }],
        ['bold', 'italic', 'underline'],
        ['link', 'image'],
        [{ list: 'ordered' }, { list: 'bullet' }],
        ['clean']
      ]
    }
  });

  // By ChatGPT for a debug
  var form = document.querySelector('form');
  form.onsubmit = function () {
    var content = document.querySelector('input[name=content]');
    content.value = quill.root.innerHTML;
  };
