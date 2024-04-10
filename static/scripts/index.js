const webcamImage = document.getElementById('webcamImage');
const CxDisp = document.getElementById('posX');
const CyDisp = document.getElementById('posY');
const portsContainer = document.getElementById('ports-container');
const portsButtons = document.getElementById('button-ports-container');
const modeIndicator = document.getElementById('mode-indicator');
const modeSwitch = document.getElementById('mode-switch');
var websocket;

let webcamsrc;
let Cx, Cy;
let port="", portsList=[];
let mode = 0;

function connect() {
    websocket = new WebSocket('ws://127.0.0.1/ws');

    websocket.onmessage = function(event) {
        let terminology = event.data.substr(0, 3)
        let data = event.data.substr(3)

        if (data.length == 0) return;

        switch (terminology) {
            case "IMG":
                webcamsrc = 'data:image/jpeg;base64,' + data.replace("\n", "");
                break;
        
            case "CXD":
                Cx = data.replace("\n", "");
                break

            case "CYD":
                Cy = data.replace("\n", "");
                break

            case "PRT":
                port = data.replace("\n", "");
                break

            case "PRS":
                portsList = data.replace("\n", "").split("|")
                break

            case "MAN":
                mode = data.replace("\n", "");
                break;

            default:
                break;
        }
    }

    websocket.onerror = reconnect;
    websocket.onclose = reconnect;
}
function reconnect() {
    setTimeout(connect, 100)
}

function updateLoop() {
    // Update webcam display
    webcamImage.src = webcamsrc;
    
    // Update center position
    CxDisp.textContent = Cx;
    CyDisp.textContent = Cy;

    // Update ports
    portsContainer.innerHTML = "";
    portsButtons.innerHTML = "";
    portsList.forEach(function (element) {
        // Create ports
        var portDisplay = document.createElement('div');
        portDisplay.classList.add("port");
        if (element == port) portDisplay.classList.add("connected-port");
        portDisplay.textContent = element;
        portsContainer.appendChild(portDisplay);

        // Create buttons
        var portButton = document.createElement('div');
        portButton.classList.add("port-button");
        if (element == port) portButton.classList.add("unavailable");
        else portButton.classList.add("available");
        let elem = element;
        portButton.onpointerdown = function () {
            websocket.send("CON"+elem);
            setTimeout(function () {
                alert("Attempting to connect");
            }, 100);
        }
        portButton.textContent = "CONNECT"
        portsButtons.appendChild(portButton);
    });

    // Update mode indicator
    modeIndicator.classList.value = ""
    modeIndicator.classList.add("mode" + mode)

    setTimeout(updateLoop, 1);
}

modeSwitch.onpointerdown = function () {
    websocket.send("MAN" + String(mode ^ 1));
}

connect()
updateLoop()