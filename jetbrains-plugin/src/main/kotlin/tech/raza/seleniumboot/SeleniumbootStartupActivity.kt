package tech.raza.seleniumboot

import com.intellij.notification.NotificationGroupManager
import com.intellij.notification.NotificationType
import com.intellij.openapi.project.Project
import com.intellij.openapi.startup.StartupActivity

private const val NOTIFICATION_GROUP = "Seleniumboot MCP"

class SeleniumbootStartupActivity : StartupActivity.Background {

    override fun runActivity(project: Project) {
        val installed = InstallChecker.isInstalled()

        if (!installed) {
            showNotification(
                project,
                "Seleniumboot MCP: <b>seleniumboot-mcp</b> is not installed. " +
                "Go to <b>Tools → Seleniumboot MCP → Install / Upgrade</b> to set it up.",
                NotificationType.WARNING
            )
            return
        }

        val command = InstallChecker.resolveCommand() ?: "seleniumboot-mcp"

        if (!MCPRegistrar.isRegistered()) {
            val registered = MCPRegistrar.register(command)
            if (registered) {
                showNotification(
                    project,
                    "Seleniumboot MCP registered with AI Assistant. " +
                    "<b>Restart the IDE</b> to activate.",
                    NotificationType.INFORMATION
                )
            } else {
                showNotification(
                    project,
                    "Seleniumboot MCP is installed but could not be auto-registered. " +
                    "Go to <b>Tools → Seleniumboot MCP → Register MCP Server</b> or add it manually " +
                    "in <i>Settings → Tools → AI Assistant → MCP Servers</i>.",
                    NotificationType.WARNING
                )
            }
        }
    }

    private fun showNotification(project: Project, content: String, type: NotificationType) {
        NotificationGroupManager.getInstance()
            .getNotificationGroup(NOTIFICATION_GROUP)
            ?.createNotification("Seleniumboot MCP", content, type)
            ?.notify(project)
    }
}
