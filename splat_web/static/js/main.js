let reportsData = {};
let commandsData = {};

// Load available reports and commands
async function loadMetadata() {
    const reportsResp = await fetch('/api/reports');
    reportsData = await reportsResp.json();
    
    const commandsResp = await fetch('/api/commands');
    commandsData = await commandsResp.json();
    
    // Populate selects
    const reportSelect = document.getElementById('reportSelect');
    for (const name in reportsData) {
        const option = document.createElement('option');
        option.value = name;
        option.textContent = `${name} (${reportsData[name].size} bytes)`;
        reportSelect.appendChild(option);
    }
    
    const commandSelect = document.getElementById('commandSelect');
    for (const name in commandsData) {
        const option = document.createElement('option');
        option.value = name;
        const commandSize = commandsData[name].command_size ?? commandsData[name].size;
        option.textContent = `${name} (${commandSize} bytes)`;
        commandSelect.appendChild(option);
    }
}

async function unpackData() {
    const hexInput = document.getElementById('hexInput').value;
    const resultDiv = document.getElementById('unpackResult');
    
    try {
        const response = await fetch('/api/unpack', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ hex: hexInput })
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayUnpackResult(data.result, resultDiv);
        } else {
            displayError(data.error, resultDiv);
        }
    } catch (error) {
        displayError(error.message, resultDiv);
    }
}

function displayUnpackResult(result, div) {
    div.className = 'result show';
    
    if (result.type === 'report') {
        let html = `
            <h3>Report: ${result.name}</h3>
            <p><span class="info-badge">ID: ${result.id}</span> <span class="info-badge">Size: ${result.size} bytes</span></p>
            <div class="hex-output">${result.hex_formatted}</div>
            <h4 style="margin-top: 20px; margin-bottom: 10px;">Decoded Variables:</h4>
            <div class="search-box">
                <input type="text" id="variableSearch" placeholder="Search variables... (name, subsystem, value)" oninput="filterVariables()">
                <div class="search-info" id="searchInfo">Showing ${result.variables.length} of ${result.variables.length} variables</div>
            </div>
            <table class="data-table" id="variablesTable">
                <thead>
                    <tr>
                        <th>Variable</th>
                        <th>Subsystem</th>
                        <th>Value</th>
                        <th>Type</th>
                        <th>Scale</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        result.variables.forEach((v, index) => {
            const scaleText = v.scale ? `x${v.scale}` : 'None';
            let displayValue = v.value;
            if (typeof v.value === 'number') {
                displayValue = v.value.toFixed(4);
            }
            
            html += `
                <tr data-variable="${v.name.toLowerCase()}" 
                    data-subsystem="${v.subsystem.toLowerCase()}" 
                    data-value="${String(displayValue).toLowerCase()}"
                    data-type="${v.type.toLowerCase()}">
                    <td><strong>${v.name}</strong></td>
                    <td><span class="subsystem-badge">${v.subsystem}</span></td>
                    <td class="value-cell">${displayValue}</td>
                    <td><span class="type-badge">${v.type}</span></td>
                    <td>${scaleText}</td>
                </tr>
            `;
        });
        
        html += `
                </tbody>
            </table>
        `;
        
        div.innerHTML = html;
    } else if (result.type === 'command') {
        let html = `
            <h3>Command: ${result.name}</h3>
            <p><span class="info-badge">ID: ${result.id}</span> <span class="info-badge">${result.subsystem}</span> <span class="info-badge">Size: ${result.size} bytes</span></p>
            <div class="hex-output">${result.hex_formatted}</div>
        `;
        
        if (result.arguments.length > 0) {
            html += `
                <h4 style="margin-top: 20px; margin-bottom: 10px;">Arguments:</h4>
                <div class="search-box">
                    <input type="text" id="argumentSearch" placeholder="Search arguments... (name, value)" oninput="filterArguments()">
                    <div class="search-info" id="searchInfo">Showing ${result.arguments.length} of ${result.arguments.length} arguments</div>
                </div>
                <table class="data-table" id="argumentsTable">
                    <thead>
                        <tr>
                            <th>Argument</th>
                            <th>Value</th>
                        </tr>
                    </thead>
                    <tbody>
            `;
            
            result.arguments.forEach(a => {
                html += `
                    <tr data-argument="${a.name.toLowerCase()}" 
                        data-value="${String(a.value).toLowerCase()}">
                        <td><strong>${a.name}</strong></td>
                        <td class="value-cell">${a.value}</td>
                    </tr>
                `;
            });
            
            html += `
                    </tbody>
                </table>
            `;
        } else {
            html += '<p style="margin-top: 15px;">No arguments</p>';
        }
        
        div.innerHTML = html;
    } else {
        displayError(result.error || 'Unknown data type', div);
    }
}

function filterVariables() {
    const searchTerm = document.getElementById('variableSearch').value.toLowerCase();
    const table = document.getElementById('variablesTable');
    const rows = table.getElementsByTagName('tbody')[0].getElementsByTagName('tr');
    let visibleCount = 0;
    let totalCount = rows.length;
    
    for (let row of rows) {
        const variable = row.getAttribute('data-variable') || '';
        const subsystem = row.getAttribute('data-subsystem') || '';
        const value = row.getAttribute('data-value') || '';
        const type = row.getAttribute('data-type') || '';
        
        const searchableText = `${variable} ${subsystem} ${value} ${type}`;
        
        if (searchableText.includes(searchTerm)) {
            row.classList.remove('hidden');
            visibleCount++;
        } else {
            row.classList.add('hidden');
        }
    }
    
    document.getElementById('searchInfo').textContent = 
        `Showing ${visibleCount} of ${totalCount} variables`;
}

function filterArguments() {
    const searchTerm = document.getElementById('argumentSearch').value.toLowerCase();
    const table = document.getElementById('argumentsTable');
    const rows = table.getElementsByTagName('tbody')[0].getElementsByTagName('tr');
    let visibleCount = 0;
    let totalCount = rows.length;
    
    for (let row of rows) {
        const argument = row.getAttribute('data-argument') || '';
        const value = row.getAttribute('data-value') || '';
        
        const searchableText = `${argument} ${value}`;
        
        if (searchableText.includes(searchTerm)) {
            row.classList.remove('hidden');
            visibleCount++;
        } else {
            row.classList.add('hidden');
        }
    }
    
    document.getElementById('searchInfo').textContent = 
        `Showing ${visibleCount} of ${totalCount} arguments`;
}

function displayError(message, div) {
    div.className = 'result show error';
    div.innerHTML = `<h3>Error</h3><p>${message}</p>`;
}

function updatePackForm() {
    const type = document.getElementById('packType').value;
    document.getElementById('packFormReport').classList.remove('show');
    document.getElementById('packFormCommand').classList.remove('show');
    document.getElementById('packButton').style.display = 'none';
    document.getElementById('packResult').classList.remove('show');
    
    if (type === 'report') {
        document.getElementById('packFormReport').classList.add('show');
    } else if (type === 'command') {
        document.getElementById('packFormCommand').classList.add('show');
    }
}

function loadReportVariables() {
    const reportName = document.getElementById('reportSelect').value;
    const container = document.getElementById('reportVariables');
    
    if (!reportName) {
        container.innerHTML = '';
        document.getElementById('packButton').style.display = 'none';
        return;
    }
    
    const report = reportsData[reportName];
    let html = '<h4 style="margin-top: 15px;">Enter Values:</h4>';
    html += `
        <div class="search-box">
            <input type="text" id="reportVariableSearch" placeholder="Search variables..." oninput="filterReportVariables()">
            <div class="search-info" id="reportSearchInfo">Showing ${report.variables.length} of ${report.variables.length} variables</div>
        </div>
        <div id="reportVariablesList">
    `;
    
    report.variables.forEach(varName => {
        html += `
            <div class="variable-input" data-varname="${varName.toLowerCase()}">
                <label for="var_${varName}">${varName}:</label>
                <input type="text" id="var_${varName}" placeholder="Enter value">
            </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
    document.getElementById('packButton').style.display = 'block';
}

function filterReportVariables() {
    const searchTerm = document.getElementById('reportVariableSearch').value.toLowerCase();
    const container = document.getElementById('reportVariablesList');
    const inputs = container.getElementsByClassName('variable-input');
    let visibleCount = 0;
    let totalCount = inputs.length;
    
    for (let input of inputs) {
        const varName = input.getAttribute('data-varname') || '';
        
        if (varName.includes(searchTerm)) {
            input.style.display = 'block';
            visibleCount++;
        } else {
            input.style.display = 'none';
        }
    }
    
    document.getElementById('reportSearchInfo').textContent = 
        `Showing ${visibleCount} of ${totalCount} variables`;
}

function loadCommandArguments() {
    const commandName = document.getElementById('commandSelect').value;
    const container = document.getElementById('commandArguments');
    
    if (!commandName) {
        container.innerHTML = '';
        document.getElementById('packButton').style.display = 'none';
        return;
    }
    
    const command = commandsData[commandName];
    let html = '<h4 style="margin-top: 15px;">Enter Arguments:</h4>';
    
    if (command.arguments.length > 0) {
        html += `
            <div class="search-box">
                <input type="text" id="commandArgumentSearch" placeholder="Search arguments..." oninput="filterCommandArguments()">
                <div class="search-info" id="commandSearchInfo">Showing ${command.arguments.length} of ${command.arguments.length} arguments</div>
            </div>
            <div id="commandArgumentsList">
        `;
        
        command.arguments.forEach(argName => {
            html += `
                <div class="variable-input" data-argname="${argName.toLowerCase()}">
                    <label for="arg_${argName}">${argName}:</label>
                    <input type="text" id="arg_${argName}" placeholder="Enter value">
                </div>
            `;
        });
        
        html += '</div>';
    } else {
        html += '<p>This command has no arguments</p>';
    }
    
    container.innerHTML = html;
    document.getElementById('packButton').style.display = 'block';
}

function filterCommandArguments() {
    const searchTerm = document.getElementById('commandArgumentSearch').value.toLowerCase();
    const container = document.getElementById('commandArgumentsList');
    const inputs = container.getElementsByClassName('variable-input');
    let visibleCount = 0;
    let totalCount = inputs.length;
    
    for (let input of inputs) {
        const argName = input.getAttribute('data-argname') || '';
        
        if (argName.includes(searchTerm)) {
            input.style.display = 'block';
            visibleCount++;
        } else {
            input.style.display = 'none';
        }
    }
    
    document.getElementById('commandSearchInfo').textContent = 
        `Showing ${visibleCount} of ${totalCount} arguments`;
}

async function packData() {
    const type = document.getElementById('packType').value;
    const resultDiv = document.getElementById('packResult');
    
    try {
        let requestData = { type };
        
        if (type === 'report') {
            const reportName = document.getElementById('reportSelect').value;
            if (!reportName) {
                displayError('Please select a report', resultDiv);
                return;
            }
            
            requestData.name = reportName;
            requestData.values = {};
            
            reportsData[reportName].variables.forEach(varName => {
                const value = document.getElementById(`var_${varName}`).value;
                if (value) {
                    requestData.values[varName] = value;
                }
            });
        } else if (type === 'command') {
            const commandName = document.getElementById('commandSelect').value;
            if (!commandName) {
                displayError('Please select a command', resultDiv);
                return;
            }
            
            requestData.name = commandName;
            requestData.values = {};
            
            commandsData[commandName].arguments.forEach(argName => {
                const value = document.getElementById(`arg_${argName}`).value;
                if (value) {
                    requestData.values[argName] = value;
                }
            });
        }
        
        const response = await fetch('/api/pack', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayPackResult(data.result, resultDiv);
        } else {
            displayError(data.error, resultDiv);
        }
    } catch (error) {
        displayError(error.message, resultDiv);
    }
}

function displayPackResult(result, div) {
    div.className = 'result show';
    div.innerHTML = `
        <h3>Packed Successfully</h3>
        <p><span class="info-badge">${result.type}</span> <span class="info-badge">${result.name}</span> <span class="info-badge">${result.size} bytes</span></p>
        <div class="hex-output">${result.hex_formatted}</div>
        <p style="margin-top: 10px; word-break: break-all;"><strong>Hex string:</strong> ${result.hex}</p>
    `;
}

// Load metadata on page load
loadMetadata();
