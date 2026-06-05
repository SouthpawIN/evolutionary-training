# Hermes Agent — MCP + Home Assistant Setup & Troubleshooting

## TL;DR

The MCP server is connected (26 tools visible), but the **native `homeassistant` skill is not loaded**. MCP registers tools at the system level, but the agent needs the matching skill enabled to use them. Fix: ensure the `homeassistant` skill is installed and enabled in your config, then run `/reload_mcp` or restart.

---

## What's Actually Happening

1. **MCP Server Status:** ✅ Connected
   - `/reload_mcp` shows "26 tool(s) available from 1 server(s)" → your Home Assistant MCP server is reachable and exposing tools.

2. **Agent Tool Resolution:** ❌ Failing
   - When you say "turn on the light," the agent doesn't see any HA tools because the **skill that declares those tool schemas and handles their execution** is not active.
   - The error *"I see you've disabled all the native homeassistant skills"* is the agent telling you: the tools exist in the MCP registry, but I have no skill module loaded that knows how to call them.

3. **Root Cause:** Skills are separate from MCP server connections.
   - MCP server = tool **provider** (exposes JSON-RPC methods over stdio/HTTP).
   - Skill = Hermes **client** (loads tool metadata, validates parameters, formats calls, and dispatches to the MCP server).
   - You can have the server running but the skill disabled → tools invisible to the agent.

---

## Verify Current State

Check which skills are actually loaded/active:

```bash
# List all available skills (all skill directories under ~/.hermes/skills/)
ls ~/.hermes/skills/

# List ENABLED skills (from config.yaml)
cat ~/.hermes/config.yaml | grep -A5 "skills:"

# Or use hermes CLI if available
hermes skills list
```

You should see a `homeassistant` skill directory. If not, it's not installed.

---

## Solution Paths

### Path A — The `homeassistant` Skill Is Installed But Disabled

**Fix:** Enable it in `config.yaml`.

1. Open your profile's config:
   ```bash
   code ~/.hermes/config.yaml   # or your editor
   ```

2. Find the `skills:` section. It may look like:
   ```yaml
   skills:
     disabled:
       - homeassistant   # ← this is the problem
   ```

   Or:
   ```yaml
   skills:
     enabled:
       - web-search
       - code-quality
       # homeassistant missing here
   ```

3. **Option 1 — Move from disabled to enabled:**
   ```yaml
   skills:
     enabled:
       - homeassistant
       - web-search
       - ...
   ```

   **Option 2 — Remove from disabled list entirely** (defaults to enabled if skill dir exists):
   ```yaml
   skills:
     disabled: []   # or remove the disabled section
   ```

4. Save, then reload:
   ```bash
   /reload_mcp        # reconnects MCP servers
   /restart           # or restart Hermes completely
   ```

5. Test:
   ```
   User: list all available tools
   Agent: Should now show Home Assistant tools (light.turn_on, switch.toggle, etc.)
   ```

---

### Path B — The `homeassistant` Skill Is Not Installed

**Fix:** Install the skill.

The `homeassistant` skill is part of the core Hermes distribution. It should be present in `~/.hermes/skills/` by default. If missing, reinstall:

```bash
# If you installed via pip
pip install --upgrade --force-reinstall hermes-agent

# If you installed from git
cd ~/.hermes/hermes-agent
git pull
# Skills are copied during install; ensure they're present:
ls ~/.hermes/skills/
```

You should see a `homeassistant` directory containing `SKILL.md` and Python code.

**If still missing after reinstall**, manually copy:
```bash
# From the source repo's skills/ directory
cp -r ~/.hermes/hermes-agent/skills/homeassistant ~/.hermes/skills/
```

Then enable in config (see Path A).

---

### Path C — You Want to Use ONLY MCP (No Native Skill)

In theory, MCP tools should be callable without a native skill — but **Hermes currently requires a native skill wrapper** for each MCP server family to translate tool calls into the proper JSON-RPC format. The `homeassistant` skill provides that translation layer for HA tools.

**Workaround:** If you cannot get the native skill working, you can call MCP tools directly via a generic MCP skill, but that's more advanced and not the default UX.

---

## Config Examples

### Minimal working config with MCP + Home Assistant

```yaml
# ~/.hermes/config.yaml
models:
  default: groq/gemma-4-it

toolsets:
  - mcp  # must be enabled

mcp:
  servers:
    homeassistant:
      command: npx
      args:
        - -y
        - @home-assistant/mcp-server
        - --ha-url
        - http://homeassistant.local:8123
        - --ha-token
        - YOUR_LONG_LIVED_TOKEN

skills:
  enabled:
    - homeassistant
    - web-search
```

**Important:** The `homeassistant` skill must be listed under `skills.enabled`, even though the tools come from MCP. The skill does not need its own config block; it reads the MCP server config.

---

## Docker-Specific Considerations

You're running `v0.11.0 (2026.4.23)` in Docker. Ensure:

1. **The MCP server binary is available inside the container.**
   - `npx @home-assistant/mcp-server` must be resolvable. If the container doesn't have npx, install Node.js or use a pre-installed binary.
   - Test manually inside the container:
     ```bash
     docker exec -it hermes-container npx -y @home-assistant/mcp-server --help
     ```

2. **Network access to Home Assistant.**
   - The HA URL (`http://homeassistant.local:8123`) must be reachable from the container. Use the host network or bridge correctly.
   - Test connectivity:
     ```bash
     docker exec hermes-container curl -I http://homeassistant.local:8123
     ```

3. **Environment variables for MCP server.**
   - Some HA MCP servers need `HA_URL` and `HA_TOKEN` env vars instead of CLI args. Check the server's documentation and adjust your config:
     ```yaml
     mcp:
       servers:
         homeassistant:
           command: npx
           args: ["-y", "@home-assistant/mcp-server"]
           env:
             HA_URL: http://homeassistant.local:8123
             HA_TOKEN: YOUR_TOKEN
     ```

4. **Permissions for the skill directory.**
   ```bash
   docker exec hermes-container ls -la ~/.hermes/skills/homeassistant
   # Should be readable by the Hermes user inside the container.
   ```

---

## Debug Steps

If the above doesn't work, gather diagnostics:

1. **Check skill loading logs:**
   ```bash
   tail -50 ~/.hermes/logs/hermes.log | grep -i homeassistant
   ```

2. **List ALL recognized tools from all sources:**
   ```
   User: what tools are available?
   Agent: Should list MCP tools + built-in tools. If HA tools missing, skill not loaded.
   ```

3. **Force-reload both MCP and skills:**
   ```
   /reload_mcp
   /reload_skills   # if such a command exists
   /restart
   ```

4. **Inspect the skill directly:**
   ```bash
   cat ~/.hermes/skills/homeassistant/SKILL.md
   # Should describe the skill and its tools.
   ```

5. **Test the MCP server standalone (outside Hermes):**
   ```bash
   echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' |      npx -y @home-assistant/mcp-server --ha-url http://homeassistant.local:8123 --ha-token YOUR_TOKEN
   # Should return a JSON list of 26 tools. If this fails, the MCP server itself is misconfigured.
   ```

---

## Common Pitfalls

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| MCP reconnects, but tools still missing | `homeassistant` skill not in `enabled` list | Add to `skills.enabled` |
| `hermes skills list` shows no homeassistant | Skill directory missing | Reinstall or copy skill from repo |
| Tools appear but calls fail with "unknown tool" | MCP server config wrong (wrong URL/token) | Verify HA URL and token; test with standalone echo command |
| Agent says "I've disabled native homeassistant skills" | HA skill exists but explicitly disabled in config | Remove from `skills.disabled` or add to `skills.enabled` |
| Docker can't find `npx` | Node.js not installed in container | Install Node.js or use a different MCP server binary |
| 26 tools show in `/reload_mcp` but agent ignores them | Skill is disabled, not just missing | Enable skill; MCP server and skill are separate concerns |

---

## Advanced: Manually Register MCP Tools Without Native Skill

If for some reason you cannot enable the native skill, you can use the generic `native-mcp` skill to call arbitrary MCP servers directly — but this requires you to know the exact tool names and parameter schemas. Example:

```yaml
# Use native-mcp as a passthrough
skills:
  enabled:
    - native-mcp   # instead of homeassistant
```

However, `native-mcp` is designed for **configuring** MCP servers, not as a user-facing skill for daily commands. The `homeassistant` skill provides friendly names, aliases, and response formatting. **Use the native skill.**

---

## Quick Checklist

- [ ] `~/.hermes/skills/homeassistant/` directory exists
- [ ] `config.yaml` lists `homeassistant` under `skills.enabled`
- [ ] `config.yaml` does **not** list `homeassistant` under `skills.disabled`
- [ ] MCP server block in `config.yaml` has correct HA URL and token
- [ ] Docker container can reach Home Assistant (test with `curl`)
- [ ] Node.js/npx available in container if using `@home-assistant/mcp-server`
- [ ] After changes: `/reload_mcp` → `/restart`
- [ ] Test: "list tools" or "turn on living room light"

---

## Final Word

MCP brought the tools to the door (26 tools connected). The `homeassistant` skill is the key that unlocks them. Enable it, and the agent will immediately start speaking the language of your smart home.

If problems persist after enabling the skill, share your `config.yaml` (redact tokens) and the output of `hermes skills list` for deeper diagnosis.

