from sigma.plugins import SigmaPluginDirectory
plugins = SigmaPluginDirectory.default_plugin_directory()
plugins.get_plugin_by_id("pysigma-backend-cortexxsiam").install()
