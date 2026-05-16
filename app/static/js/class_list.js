// class_list.js
// Client-side handling for temporary cancellation of enrollments.
// Clicking the X removes the row on the client and stores the enrollment id
// in a transient list. Only when the user clicks Confirm (and the form is
// submitted) the canceled ids are sent to the server to be persisted.

document.addEventListener('DOMContentLoaded', function () {
  var canceled = new Set();

  function updateSummary(deltaCredits, deltaCount) {
	var creditsEl = document.getElementById('total-credits');
	var coursesEl = document.getElementById('total-courses');

	if (creditsEl) {
	  // total-credits has format like "12 / 25"
	  var parts = creditsEl.textContent.split('/');
	  var current = parseInt(parts[0]) || 0;
	  current = Math.max(0, current + (deltaCredits || 0));
	  creditsEl.textContent = current + ' / 25';
	}

	if (coursesEl) {
	  var c = parseInt(coursesEl.textContent) || 0;
	  c = Math.max(0, c + (deltaCount || 0));
	  coursesEl.textContent = c;
	}
  }

  function ensureEmptyMessage() {
	var tbody = document.querySelector('#registered-courses tbody');
	if (!tbody) return;
	// count tr elements that are not the "empty" message
	var rows = tbody.querySelectorAll('tr');
	if (rows.length === 0) {
	  var tr = document.createElement('tr');
	  var td = document.createElement('td');
	  td.setAttribute('colspan', '6');
	  td.style.textAlign = 'center';
	  td.style.padding = '20px';
	  td.textContent = 'Sinh viên chưa đăng ký môn học nào.';
	  tr.appendChild(td);
	  tbody.appendChild(tr);
	}
  }

  // Attach cancel handlers
  document.querySelectorAll('.btn-cancel').forEach(function (btn) {
	btn.addEventListener('click', function (e) {
	  var id = btn.getAttribute('data-enrollment-id');
	  if (!id) return;

	  var tr = btn.closest('tr');
	  var credit = 0;
	  if (tr && tr.dataset && tr.dataset.credit) {
		credit = parseInt(tr.dataset.credit) || 0;
	  }

	  // Add to canceled set
	  canceled.add(id);

	  // Remove row from DOM
	  if (tr) tr.remove();

	  // Update summary
	  updateSummary(-credit, -1);

	  ensureEmptyMessage();
	});
  });

  // Before submitting the confirm form, append hidden inputs for canceled ids
  var confirmForm = document.getElementById('confirm-form');
  if (confirmForm) {
	confirmForm.addEventListener('submit', function (ev) {
	  // Append one hidden input per canceled id
	  canceled.forEach(function (id) {
		var inp = document.createElement('input');
		inp.type = 'hidden';
		inp.name = 'canceled_ids';
		inp.value = id;
		confirmForm.appendChild(inp);
	  });
	});
  }
});
