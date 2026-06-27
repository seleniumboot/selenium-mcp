package io.github.seleniumboot.mcp

import com.intellij.notification.NotificationGroupManager
import com.intellij.notification.NotificationType
import com.intellij.openapi.project.Project
import com.intellij.openapi.startup.ProjectActivity

class SeleniumbootStartupActivity : ProjectActivity {

    override suspend fun execute(project: Project) {
        val installed = InstallChecker.isInstalled()

        if (!installed) {
            showNotification(
                project,
                "Selenium Boot MCP: <b>seleniumboot-mcp</b> is not installed. " +
                "Go to <b>Tools → Selenium Boot MCP → Install / Upgrade</b> to set it up.",
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
                    "Selenium Boot MCP registered with AI Assistant. " +
                    "<b>Restart the IDE</b> to activate.",
                    NotificationType.INFORMATION
                )
            } else {
                showNotification(
                    project,
                    "Selenium Boot MCP is installed but could not be auto-registered. " +
                    "Go to <b>Tools → Selenium Boot MCP → Register MCP Server</b> or add it manually " +
                    "in <i>Settings → Tools → AI Assistant → MCP Servers</i>.",
                    NotificationType.WARNING
                )
            }
        }
    }

    private fun showNotification(project: Project, content: String, type: NotificationType) {
        NotificationGroupManager.getInstance()
            .getNotificationGroup(NOTIFICATION_GROUP)
            ?.createNotification("Selenium Boot MCP", content, type)
            ?.notify(project)
    }
}
