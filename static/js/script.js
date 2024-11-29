// Fetch current date from the server
fetch('/get_current_date')
    .then(response => response.json())
    .then(data => {
        document.getElementById('currentDate').textContent = data.date;
    });

// Load students automatically
function loadStudents() {
    fetch('/get_students')
        .then(response => response.json())
        .then(data => {
            const studentsList = document.getElementById('students');
            studentsList.innerHTML = '';
            data.students.forEach(student => {
                const li = document.createElement('li');
                li.textContent = `${student.name} - PRN: ${student.prn}`;
                li.dataset.id = student.id;  // Store the student ID
                li.classList.add('student-item');  // Add a class for styling

                // Click event to select the student
                li.addEventListener('click', () => {
                    document.querySelectorAll('#students li').forEach(item => {
                        item.classList.remove('selected');
                    });
                    li.classList.add('selected');  // Highlight selected student
                });

                studentsList.appendChild(li);
            });
        });
}

// Automatically load students on page load
loadStudents();

let videoStream; // Variable to hold the video stream

// Function to start the webcam
function startWebcam() {
    const videoElement = document.getElementById('webcam');
    navigator.mediaDevices.getUserMedia({ video: true })
        .then(stream => {
            videoStream = stream;
            videoElement.srcObject = stream;
        })
        .catch(error => {
            console.error("Error accessing the webcam:", error);
            alert("Could not access the webcam. Please check your permissions.");
        });
}

// Function to stop the webcam
function stopWebcam() {
    if (videoStream) {
        videoStream.getTracks().forEach(track => track.stop());
        videoStream = null;
    }
}

// Add event listeners to buttons
document.getElementById('startBtn').addEventListener('click', startWebcam);
document.getElementById('stopBtn').addEventListener('click', stopWebcam);

// Function to handle face detection (placeholder)
function onFaceDetected(student) {
    const studentsList = document.getElementById('students');
    const studentItem = document.createElement('li');
    studentItem.textContent = `${student.name} - PRN: ${student.prn} (Attendance Marked)`;
    studentItem.classList.add('attendance-marked');  // For styling marked attendance

    // Mark attendance on face detection
    fetch('/mark_attendance', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            student_id: student.id,
            date: new Date().toLocaleDateString(),
            time: new Date().toLocaleTimeString() // Adjust if needed
        }),
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        loadStudents(); // Refresh the students list to show attendance marked
    });
}

// Placeholder for face detection logic
// Call onFaceDetected with the detected student data
// Example: onFaceDetected({ id: 1, name: 'John Doe', prn: 'PRN12345' });
