package io.github.seleniumboot.mcp

import com.intellij.notification.NotificationGroupManager
import com.intellij.notification.NotificationType
import com.intellij.openapi.actionSystem.AnAction
import com.intellij.openapi.actionSystem.AnActionEvent
import com.intellij.openapi.project.Project

private const val INSTALL_CMD = "pip install --upgrade seleniumboot-mcp"
internal const val NOTIFICATION_GROUP = "Selenium Boot MCP"

class InstallAction : AnAction() {
    override fun actionPerformed(e: AnActionEvent) {
        val project = e.project ?: return
        runPipCommand(project, INSTALL_CMD)
    }
}

class RegisterMCPAction : AnAction() {
    override fun actionPerformed(e: AnActionEvent) {
        val project = e.project ?: return
        val command = InstallChecker.resolveCommand() ?: "seleniumboot-mcp"
        val ok = MCPRegistrar.register(command)
        if (ok) {
            notify(project, "Registered successfully. Restart the IDE to activate.", NotificationType.INFORMATION)
        } else {
            notify(
                project,
                "Could not auto-register. Add manually in <i>Settings → Tools → AI Assistant → MCP Servers</i>. " +
                "Command: <code>seleniumboot-mcp</code>",
                NotificationType.ERROR
            )
        }
    }
}

class CheckStatusAction : AnAction() {
    override fun actionPerformed(e: AnActionEvent) {
        val project = e.project ?: return
        val installed = InstallChecker.isInstalled()
        val registered = MCPRegistrar.isRegistered()
        val msg = buildString {
            append(if (installed) "✓ seleniumboot-mcp is installed. " else "✗ seleniumboot-mcp is NOT installed. ")
            append(if (registered) "✓ Registered with AI Assistant." else "✗ Not yet registered.")
        }
        notify(
            project, msg,
            if (installed && registered) NotificationType.INFORMATION else NotificationType.WARNING
        )
    }
}

private fun runPipCommand(project: Project, command: String) {
    try {
        val isWindows = System.getProperty("os.name").lowercase().contains("win")
        val proc = if (isWindows) {
            ProcessBuilder("cmd", "/c", command)
        } else {
            ProcessBuilder("bash", "-c", command)
        }
        proc.redirectErrorStream(true).start()
        notify(project, "Running: <code>$command</code> — check your terminal for output.", NotificationType.INFORMATION)
    } catch (ex: Exception) {
        notify(project, "Failed to run: $command<br>${ex.message}", NotificationType.ERROR)
    }
}

private fun notify(project: Project, content: String, type: NotificationType) {
    NotificationGroupManager.getInstance()
        .getNotificationGroup(NOTIFICATION_GROUP)
        ?.createNotification("Selenium Boot MCP", content, type)
        ?.notify(project)
}
