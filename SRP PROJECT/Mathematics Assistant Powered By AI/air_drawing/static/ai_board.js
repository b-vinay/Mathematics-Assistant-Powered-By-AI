const canvas = document.getElementById('canvas');
const brushSize = document.getElementById('brush-size');
const colorPicker = document.getElementById('color-picker');
const eraser = document.getElementById('eraser');
const clear = document.getElementById('clear');
const download = document.getElementById('download');
const solve = document.getElementById('solve');
const solutionOutput = document.getElementById('solution-output');
const previewBox = document.getElementById('preview-box');

let drawing = false;
let currentColor = colorPicker.value;
let currentSize = brushSize.value;
const ctx = canvas.getContext('2d');


canvas.addEventListener('mousedown', (e) => {
    drawing = true;
    ctx.beginPath(); // Start a new path on mouse down
    draw(e); // Start drawing immediately
});

canvas.addEventListener('mouseup', () => {
    drawing = false;
});

canvas.addEventListener('mouseout', () => {
    drawing = false;
});

canvas.addEventListener('mousemove', draw);

colorPicker.addEventListener('change', () => {
    currentColor = colorPicker.value;
});

brushSize.addEventListener('change', () => {
    currentSize = brushSize.value;
});

eraser.addEventListener('click', () => {
    currentColor = '#ffffff';
});

clear.addEventListener('click', () => {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
});

// download.addEventListener('click', () => {
//     // Create a temporary canvas
//     const tempCanvas = document.createElement('canvas');
//     const tempCtx = tempCanvas.getContext('2d');

//     tempCanvas.width = canvas.width;
//     tempCanvas.height = canvas.height;

//     // Fill background with white
//     tempCtx.fillStyle = '#ffffff';
//     tempCtx.fillRect(0, 0, tempCanvas.width, tempCanvas.height);

//     // Draw the original canvas on top
//     tempCtx.drawImage(canvas, 0, 0);

//     // Convert to image and download
//     const link = document.createElement('a');
//     link.download = 'canvas.png';
//     link.href = tempCanvas.toDataURL('image/png');
//     link.click();
// });

solve.addEventListener('click', () => {
    const loading = document.getElementById('loading');
    const solutionOutput = document.getElementById('solution-output');

    // Show loading message and clear previous result
    loading.style.display = 'block';
    solutionOutput.textContent = '';
    previewBox.style.display = 'block';

    // Create a temp canvas with white background
    const tempCanvas = document.createElement('canvas');
    const tempCtx = tempCanvas.getContext('2d');

    tempCanvas.width = canvas.width;
    tempCanvas.height = canvas.height;

    tempCtx.fillStyle = '#ffffff';
    tempCtx.fillRect(0, 0, tempCanvas.width, tempCanvas.height);
    tempCtx.drawImage(canvas, 0, 0);

    tempCanvas.toBlob((blob) => {
        const formData = new FormData();
        formData.append('image', blob, 'drawing.png');

        fetch('/solve', {
            method: 'POST',
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            // Hide loading, show solution
            loading.style.display = 'none';
            solutionOutput.textContent = data.result;
        })
        .catch(err => {
            console.error('Error:', err);
            loading.style.display = 'none';
            solutionOutput.textContent = 'An error occurred while solving the problem.';
        });
    }, 'image/png');
});


function draw(e) {
    if (!drawing) return;

    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    ctx.lineTo(x, y);
    ctx.strokeStyle = currentColor;
    ctx.lineWidth = currentSize;
    ctx.lineCap = 'round';
    ctx.stroke();

    // Move to current point for next segment
    ctx.beginPath();
    ctx.moveTo(x, y);
}
