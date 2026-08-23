import * as vscode from 'vscode';
import { exec } from 'child_process';
import { promisify } from 'util';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';

const execAsync = promisify(exec);

const INSTALL_CMD = 'pip install seleniumboot-mcp';
const UPGRADE_CMD = 'pip install --upgrade seleniumboot-mcp';
const MCP_SERVER_KEY = 'seleniumboot';

async function isInstalled(): Promise<boolean> {
    const checks = [
        'python3 -c "import selenium_mcp"',
        'python -c "import selenium_mcp"',
        'pip show seleniumboot-mcp',
        'pip3 show seleniumboot-mcp',
    ];
    for (const cmd of checks) {
        try {
            await execAsync(cmd);
            return true;
        } catch {
            // try next
        }
    }
    return false;
}

async function resolveCommand(): Promise<string> {
    // Prefer full path so Claude Code can find it even when PATH differs
    for (const cmd of ['seleniumboot-mcp', 'seleniumboot-mcp3']) {
        try {
            const { stdout } = await execAsync(
                process.platform === 'win32' ? `where ${cmd}` : `which ${cmd}`
            );
            const resolved = stdout.trim().split('\n')[0].trim();
            if (resolved) return resolved;
        } catch { /* try next */ }
    }
    return 'seleniumboot-mcp'; // fallback — rely on PATH
}

function writeMcpEntry(filePath: string, command: string): boolean {
    try {
        const dir = path.dirname(filePath);
        if (!fs.existsSync(dir)) {
            fs.mkdirSync(dir, { recursive: true });
        }
        let settings: Record<string, unknown> = {};
        if (fs.existsSync(filePath)) {
            try {
                settings = JSON.parse(fs.readFileSync(filePath, 'utf8'));
            } catch {
                // The file exists but isn't valid JSON — it may be hand-edited or
                // commented out on purpose. Leave it alone rather than overwriting.
                return false;
            }
        }
        const mcpServers = (settings['mcpServers'] as Record<string, unknown> | undefined) ?? {};
        const existing = mcpServers[MCP_SERVER_KEY] as { command?: string } | undefined;
        if (existing?.command === command) return true; // already up to date
        mcpServers[MCP_SERVER_KEY] = { command, args: [] };
        settings['mcpServers'] = mcpServers;
        fs.writeFileSync(filePath, JSON.stringify(settings, null, 4), 'utf8');
        return true;
    } catch {
        return false;
    }
}

/**
 * Register with Claude Code.
 *
 * ~/.claude/settings.json — global (CLI + VS Code extension user scope) — is
 * enough on its own: Claude Code reads it for every project. A project-level
 * <workspace>/.mcp.json is also supported, but it drops an untracked file into
 * every workspace that's opened, so it's opt-in via
 * `seleniumbootMcp.registerProjectMcpJson`.
 */
async function registerWithClaudeCode(command: string): Promise<void> {
    // Global user settings
    const globalSettings = path.join(os.homedir(), '.claude', 'settings.json');
    writeMcpEntry(globalSettings, command);

    const writeProjectFiles = vscode.workspace
        .getConfiguration('seleniumbootMcp')
        .get<boolean>('registerProjectMcpJson', false);
    if (!writeProjectFiles) return;

    // Project-level .mcp.json for each open workspace folder
    const folders = vscode.workspace.workspaceFolders ?? [];
    for (const folder of folders) {
        const mcpJson = path.join(folder.uri.fsPath, '.mcp.json');
        writeMcpEntry(mcpJson, command);
    }
}

function openTerminalAndRun(command: string) {
    const terminal = vscode.window.createTerminal('Seleniumboot MCP Setup');
    terminal.show();
    terminal.sendText(command);
}

export async function activate(context: vscode.ExtensionContext) {
    const installed = await isInstalled();

    if (!installed) {
        const action = await vscode.window.showWarningMessage(
            'Seleniumboot MCP: The `seleniumboot-mcp` Python package is not installed. ' +
            'Install it to enable Selenium browser automation for Copilot and Claude.',
            'Install via pip',
            'Show instructions'
        );

        if (action === 'Install via pip') {
            openTerminalAndRun(INSTALL_CMD);
        } else if (action === 'Show instructions') {
            vscode.env.openExternal(
                vscode.Uri.parse('https://github.com/seleniumboot/selenium-mcp#installation')
            );
        }
        return; // don't register until package is actually installed
    }

    // Auto-register with Claude Code (global settings; project .mcp.json only if opted in)
    const command = await resolveCommand();
    await registerWithClaudeCode(command);
    console.log(`Seleniumboot MCP: registered "${command}"`);

    // Command: manually trigger install
    context.subscriptions.push(
        vscode.commands.registerCommand('seleniumboot-mcp.install', () => {
            openTerminalAndRun(INSTALL_CMD);
        })
    );

    // Command: upgrade
    context.subscriptions.push(
        vscode.commands.registerCommand('seleniumboot-mcp.upgrade', () => {
            openTerminalAndRun(UPGRADE_CMD);
        })
    );

    // Command: check status
    context.subscriptions.push(
        vscode.commands.registerCommand('seleniumboot-mcp.checkStatus', async () => {
            const ok = await isInstalled();
            if (ok) {
                vscode.window.showInformationMessage(
                    'Seleniumboot MCP: seleniumboot-mcp is installed and ready. ' +
                    'MCP server is registered in ~/.claude/settings.json.'
                );
            } else {
                const install = await vscode.window.showWarningMessage(
                    'Seleniumboot MCP: seleniumboot-mcp is not installed.',
                    'Install now'
                );
                if (install) openTerminalAndRun(INSTALL_CMD);
            }
        })
    );
}

export function deactivate() {}
