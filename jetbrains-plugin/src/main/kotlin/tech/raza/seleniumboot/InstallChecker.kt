package tech.raza.seleniumboot

object InstallChecker {

    fun isInstalled(): Boolean {
        val checks = listOf(
            listOf("python3", "-c", "import selenium_mcp"),
            listOf("python", "-c", "import selenium_mcp"),
            listOf("pip", "show", "seleniumboot-mcp"),
            listOf("pip3", "show", "seleniumboot-mcp"),
        )
        return checks.any { runSilently(it) }
    }

    fun resolveCommand(): String? {
        for (cmd in listOf("seleniumboot-mcp", "seleniumboot-mcp3")) {
            val which = if (isWindows()) listOf("where", cmd) else listOf("which", cmd)
            val output = runCapture(which)?.trim()
            if (!output.isNullOrEmpty()) return output.lines().first().trim()
        }
        return null
    }

    private fun runSilently(cmd: List<String>): Boolean = try {
        ProcessBuilder(cmd)
            .redirectErrorStream(true)
            .start()
            .waitFor() == 0
    } catch (_: Exception) {
        false
    }

    private fun runCapture(cmd: List<String>): String? = try {
        val proc = ProcessBuilder(cmd).redirectErrorStream(true).start()
        val out = proc.inputStream.bufferedReader().readText()
        if (proc.waitFor() == 0) out else null
    } catch (_: Exception) {
        null
    }

    private fun isWindows() = System.getProperty("os.name").lowercase().contains("win")
}
