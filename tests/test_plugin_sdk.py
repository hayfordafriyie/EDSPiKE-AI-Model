from src.plugin.sdk import PluginSDK, PluginManifest, PLUGIN_SDK


class TestPluginSDK:
    def test_register_manifest(self):
        sdk = PluginSDK()
        m = PluginManifest(name="test", version="1.0.0", description="Test plugin")
        sdk.register(m)
        assert sdk.get_manifest("test") is not None

    def test_hook_emit(self):
        sdk = PluginSDK()
        results = []
        sdk.on("before_tool", lambda tool: results.append(tool))
        sdk.emit("before_tool", "bash")
        assert results == ["bash"]

    def test_emit_multiple_hooks(self):
        sdk = PluginSDK()
        sdk.on("event", lambda: "a")
        sdk.on("event", lambda: "b")
        results = sdk.emit("event")
        assert results == ["a", "b"]

    def test_state(self):
        sdk = PluginSDK()
        sdk.set_state("key", "val")
        assert sdk.get_state("key") == "val"
        assert sdk.get_state("missing", "default") == "default"

    def test_has_hook(self):
        sdk = PluginSDK()
        assert sdk.has_hook("nonexistent") is False
        sdk.on("test", lambda: None)
        assert sdk.has_hook("test") is True

    def test_list_plugins(self):
        sdk = PluginSDK()
        sdk.register(PluginManifest(name="a", version="1", description=""))
        sdk.register(PluginManifest(name="b", version="2", description=""))
        assert len(sdk.list_plugins()) == 2
