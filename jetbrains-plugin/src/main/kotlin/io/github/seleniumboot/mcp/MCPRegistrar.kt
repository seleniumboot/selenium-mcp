package io.github.seleniumboot.mcp

import com.intellij.openapi.application.PathManager
import org.w3c.dom.Document
import org.w3c.dom.Element
import java.io.File
import javax.xml.parsers.DocumentBuilderFactory
import javax.xml.transform.OutputKeys
import javax.xml.transform.TransformerFactory
import javax.xml.transform.dom.DOMSource
import javax.xml.transform.stream.StreamResult

private const val COMPONENT_NAME = "McpApplicationServerCommands"
private const val SERVER_NAME = "seleniumboot"
private const val MCP_FILE = "llm.mcpServers.xml"

object MCPRegistrar {

    fun isRegistered(): Boolean {
        val file = mcpConfigFile() ?: return false
        if (!file.exists()) return false
        return file.readText().contains("seleniumboot")
    }

    fun register(command: String): Boolean {
        return try {
            val file = mcpConfigFile() ?: return false
            val doc = loadOrCreate(file)
            val root = doc.documentElement

            val component = findOrCreateComponent(doc, root)
            val commands = findOrCreateElement(doc, component, "commands")

            // Remove existing entry with same name to avoid duplicates
            val existing = commands.getElementsByTagName("*")
            for (i in existing.length - 1 downTo 0) {
                val node = existing.item(i) as? Element ?: continue
                if (node.getAttribute("name") == SERVER_NAME) {
                    commands.removeChild(node)
                }
            }

            val entry = doc.createElement("McpServerStdioCommand")
            entry.setAttribute("name", SERVER_NAME)
            entry.setAttribute("command", command)
            entry.setAttribute("args", "")
            entry.setAttribute("enabled", "true")
            commands.appendChild(entry)

            writeXml(doc, file)
            true
        } catch (_: Exception) {
            false
        }
    }

    private fun mcpConfigFile(): File? {
        val optionsPath = PathManager.getOptionsPath()
        return if (optionsPath.isNotEmpty()) File(optionsPath, MCP_FILE) else null
    }

    private fun loadOrCreate(file: File): Document {
        if (file.exists()) {
            return try {
                DocumentBuilderFactory.newInstance().newDocumentBuilder().parse(file)
            } catch (_: Exception) {
                newDocument()
            }
        }
        return newDocument()
    }

    private fun newDocument(): Document {
        val doc = DocumentBuilderFactory.newInstance().newDocumentBuilder().newDocument()
        doc.appendChild(doc.createElement("application"))
        return doc
    }

    private fun findOrCreateComponent(doc: Document, root: Element): Element {
        val list = root.getElementsByTagName("component")
        for (i in 0 until list.length) {
            val el = list.item(i) as? Element ?: continue
            if (el.getAttribute("name") == COMPONENT_NAME) return el
        }
        val el = doc.createElement("component")
        el.setAttribute("name", COMPONENT_NAME)
        el.setAttribute("modifiable", "true")
        el.setAttribute("autoEnableExternalChanges", "false")
        root.appendChild(el)
        return el
    }

    private fun findOrCreateElement(doc: Document, parent: Element, tag: String): Element {
        val list = parent.getElementsByTagName(tag)
        if (list.length > 0) return list.item(0) as Element
        val el = doc.createElement(tag)
        parent.appendChild(el)
        return el
    }

    private fun writeXml(doc: Document, file: File) {
        file.parentFile?.mkdirs()
        val transformer = TransformerFactory.newInstance().newTransformer()
        transformer.setOutputProperty(OutputKeys.INDENT, "yes")
        transformer.setOutputProperty("{http://xml.apache.org/xslt}indent-amount", "2")
        transformer.transform(DOMSource(doc), StreamResult(file))
    }
}
