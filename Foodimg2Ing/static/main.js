// Elements
const hiddenFileInput = document.getElementById("hiddenFileInput");
const foodUploadForm = document.getElementById("foodUploadForm");
const dropzoneBox = document.getElementById("dropzoneBox");
const imagePreviewEl = document.getElementById("imagePreviewEl");
const dropzonePlaceholder = document.getElementById("dropzonePlaceholder");
const clearPreviewBtn = document.getElementById("clearPreviewBtn");
const uploadErrorMsg = document.getElementById("uploadErrorMsg");
const submitUploadBtn = document.getElementById("submitUploadBtn");
const submitBtnText = document.getElementById("submitBtnText");

let selectedFileObj = null;

// Trigger file picker
function triggerFileSelect() {
    if (hiddenFileInput) {
        hiddenFileInput.click();
    }
}

// Handle file input change
if (hiddenFileInput) {
    hiddenFileInput.addEventListener("change", function () {
        if (this.files && this.files[0]) {
            handleFileSelection(this.files[0]);
        }
    });
}

// Display chosen image inside dropzone
function handleFileSelection(file) {
    if (!file || !file.type.startsWith("image/")) {
        showInlineError("Please select a valid image file.");
        return;
    }
    
    hideInlineError();
    selectedFileObj = file;

    const reader = new FileReader();
    reader.onload = function (e) {
        if (imagePreviewEl) {
            imagePreviewEl.src = e.target.result;
            imagePreviewEl.style.display = "block";
        }
        if (dropzonePlaceholder) {
            dropzonePlaceholder.style.display = "none";
        }
        if (clearPreviewBtn) {
            clearPreviewBtn.style.display = "flex";
        }
    };
    reader.readAsDataURL(file);
}

// Drag and drop event listeners
if (dropzoneBox) {
    ['dragenter', 'dragover'].forEach(eventName => {
        dropzoneBox.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzoneBox.classList.add('dragover');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzoneBox.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzoneBox.classList.remove('dragover');
        }, false);
    });

    dropzoneBox.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        if (dt && dt.files && dt.files[0]) {
            const file = dt.files[0];
            // Assign to input files using DataTransfer
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(file);
            hiddenFileInput.files = dataTransfer.files;
            handleFileSelection(file);
        }
    }, false);
}

// Clear preview
function clearSelectedImage(event) {
    if (event) event.stopPropagation();
    selectedFileObj = null;
    if (hiddenFileInput) hiddenFileInput.value = "";
    if (imagePreviewEl) {
        imagePreviewEl.src = "";
        imagePreviewEl.style.display = "none";
    }
    if (dropzonePlaceholder) {
        dropzonePlaceholder.style.display = "block";
    }
    if (clearPreviewBtn) {
        clearPreviewBtn.style.display = "none";
    }
    hideInlineError();
}

// Submit button handler
function handleUploadSubmit() {
    // If no file has been chosen yet, trigger the file picker or show error
    if (!hiddenFileInput.files || hiddenFileInput.files.length === 0) {
        // If nothing selected, trigger file picker first
        triggerFileSelect();
        showInlineError("Choose a photo first.");
        return;
    }

    hideInlineError();
    setButtonLoadingState();
    if (foodUploadForm) {
        foodUploadForm.submit();
    }
}

// Inline error message
function showInlineError(msg) {
    if (uploadErrorMsg) {
        uploadErrorMsg.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${msg}`;
        uploadErrorMsg.style.display = "block";
    }
}

function hideInlineError() {
    if (uploadErrorMsg) {
        uploadErrorMsg.style.display = "none";
    }
}

// Loading state
function setButtonLoadingState() {
    if (submitUploadBtn) {
        submitUploadBtn.disabled = true;
        submitUploadBtn.style.opacity = "0.9";
        submitUploadBtn.innerHTML = `
            <span class="spinner-border-sm"></span>
            <span>Analyzing your dish…</span>
        `;
    }
}

// Sample dish selection
function handleSampleClick(filename) {
    if (imagePreviewEl) {
        imagePreviewEl.src = `/static/images/${filename}`;
        imagePreviewEl.style.display = "block";
    }
    if (dropzonePlaceholder) {
        dropzonePlaceholder.style.display = "none";
    }
    setButtonLoadingState();
}

// Recipe tabs switcher
function switchRecipeTab(tabNum) {
    const tab1 = document.getElementById("recipeTab1");
    const tab2 = document.getElementById("recipeTab2");
    const btn1 = document.getElementById("tabbtn1");
    const btn2 = document.getElementById("tabbtn2");

    if (tabNum === 1) {
        if (tab1) tab1.style.display = "block";
        if (tab2) tab2.style.display = "none";
        if (btn1) btn1.className = "recipe-tab-btn active";
        if (btn2) btn2.className = "recipe-tab-btn";
    } else {
        if (tab1) tab1.style.display = "none";
        if (tab2) tab2.style.display = "block";
        if (btn1) btn1.className = "recipe-tab-btn";
        if (btn2) btn2.className = "recipe-tab-btn active";
    }
}
