const vscode = require('vscode');

function activate(context) {
    const apiUrl = vscode.workspace.getConfiguration('edspike').get('apiUrl') || 'http://localhost:8000';
    const apiKey = vscode.workspace.getConfiguration('edspike').get('apiKey') || '';

    async function callApi(prompt) {
        const response = await fetch(`${apiUrl}/v1/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...(apiKey && { 'Authorization': `Bearer ${apiKey}` })
            },
            body: JSON.stringify({ prompt, max_tokens: 2048 })
        });
        const data = await response.json();
        return data.response || '(no response)';
    }

    function getSelectedText() {
        const editor = vscode.window.activeTextEditor;
        return editor ? editor.document.getText(editor.selection) : '';
    }

    async function askQuestion() {
        const prompt = await vscode.window.showInputBox({
            prompt: 'Ask EDSPiKE AI Agent',
            placeHolder: 'Type your question...'
        });
        if (!prompt) return;

        vscode.window.withProgress({ location: vscode.ProgressLocation.Notification, title: 'EDSPiKE thinking...' }, async () => {
            try {
                const response = await callApi(prompt);
                const doc = await vscode.workspace.openTextDocument({ content: response, language: 'markdown' });
                vscode.window.showTextDocument(doc, { viewColumn: vscode.ViewColumn.Beside });
            } catch (err) {
                vscode.window.showErrorMessage(`EDSPiKE error: ${err.message}`);
            }
        });
    }

    async function explainCode() {
        const selection = getSelectedText();
        if (!selection) {
            vscode.window.showInformationMessage('Select code to explain.');
            return;
        }
        vscode.window.withProgress({ location: vscode.ProgressLocation.Notification, title: 'EDSPiKE explaining...' }, async () => {
            try {
                const response = await callApi(`Explain this code:\n\`\`\`\n${selection}\n\`\`\``);
                vscode.window.showInformationMessage(response.slice(0, 500));
            } catch (err) {
                vscode.window.showErrorMessage(`EDSPiKE error: ${err.message}`);
            }
        });
    }

    async function fixCode() {
        const selection = getSelectedText();
        if (!selection) {
            vscode.window.showInformationMessage('Select code to fix.');
            return;
        }
        vscode.window.withProgress({ location: vscode.ProgressLocation.Notification, title: 'EDSPiKE fixing...' }, async () => {
            try {
                const response = await callApi(`Fix this code:\n\`\`\`\n${selection}\n\`\`\``);
                const editor = vscode.window.activeTextEditor;
                if (editor) {
                    editor.edit(editBuilder => {
                        editBuilder.replace(editor.selection, response.replace(/^```[\w]*\n?|```$/gm, ''));
                    });
                }
            } catch (err) {
                vscode.window.showErrorMessage(`EDSPiKE error: ${err.message}`);
            }
        });
    }

    context.subscriptions.push(
        vscode.commands.registerCommand('edspike.ask', askQuestion),
        vscode.commands.registerCommand('edspike.explain', explainCode),
        vscode.commands.registerCommand('edspike.fix', fixCode),
        vscode.commands.registerCommand('edspike.chat', () => {
            vscode.commands.executeCommand('workbench.action.terminal.sendSequence', { text: 'edspike\n' });
        })
    );
}

function deactivate() {}

module.exports = { activate, deactivate };
