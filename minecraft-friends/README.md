# Local Minecraft Java server

This folder runs an official **vanilla Minecraft Java 26.2 dedicated server** on the computer in front of you. Friends on the same Wi-Fi join with your LAN address. Friends over the internet join through a [playit.gg](https://playit.gg) tunnel (no router port forwarding).

Pinned version: **Minecraft 26.2** (needs **Java 25**). Everyone who joins must use that same game version in the launcher.

## Quick start

### Linux / macOS

```bash
cd minecraft-friends
./scripts/install.sh
./scripts/start-server.sh
```

Then in Minecraft: **Multiplayer → Direct Connection → `localhost`**

### Windows

Right-click `windows/Start-Server.ps1` → **Run with PowerShell**.
If Windows blocks it, run this once in PowerShell:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Join at `localhost` the same way.

## Friends on the same Wi-Fi

1. Keep the server running on your PC.
2. Run `./scripts/status.sh` (or look at the start script output) for your LAN address, like `192.168.1.42:25565`.
3. Friends use **Direct Connection** with that address.
4. Windows: allow Java through the firewall when prompted, or allow inbound TCP port `25565`.

This does **not** work for friends on a different network. Use the tunnel below.

## Friends over the internet

Do **not** share your home IP. Use the tunnel:

```bash
./scripts/open-to-friends.sh
```

On Windows, run `windows/Open-To-Friends.ps1`.

The script prints a `https://playit.gg/claim/...` link. Open it, claim the agent, then **Add Tunnel → Minecraft Java** pointing at `127.0.0.1:25565`. Send friends the public address playit shows (not `localhost`).

`prevent-proxy-connections` is already off in `templates/server.properties` so tunnel joins work.

## Useful commands

| Action | Linux / macOS |
| --- | --- |
| Start | `./scripts/start-server.sh` |
| Stop | `./scripts/stop.sh` |
| Is it up? | `./scripts/status.sh` |
| Make yourself operator | `./scripts/console.sh 'op YourMinecraftName'` |
| Whitelist a friend | `./scripts/console.sh 'whitelist add TheirName'` then `'whitelist on'` |
| Attach to the live console | `tmux attach -t minecraft-server` (then `Ctrl-b` `d` to detach) |

World files live in `runtime/` (gitignored). Do not commit them.

## Singleplayer "Open to LAN" instead

If you only need a few friends **in the same house** and do not want a dedicated server:

1. Open a world in Minecraft Java.
2. Pause → **Open to LAN**.
3. Friends on the same Wi-Fi see it under Multiplayer.

That session ends when you leave the world. The dedicated server in this folder stays up until you stop it.

## Bedrock / phones / consoles / Microsoft Store

This kit is **Java Edition**. The Minecraft app from the Microsoft Store, phones, and consoles are Bedrock.

- Bedrock already has **Play → Friends** (Xbox / Microsoft account).
- A Bedrock dedicated server is a different download and uses UDP port `19132`.
- Java and Bedrock cannot join each other unless you add extra software (Geyser), which this kit does not install.

## Safety

- Run with `online-mode=true` (default) so only real Minecraft accounts join.
- After friends connect, turn the whitelist on.
- This Cloud Agent machine is not a 24/7 host: if you started the server here, it goes away when the agent stops. For real play, run the scripts on your own PC.
