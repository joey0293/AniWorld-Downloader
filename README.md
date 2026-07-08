<a id="readme-top"></a>

# AniWorld Downloader v4

AniWorld Downloader is a cross-platform tool for streaming and downloading anime from aniworld.to, as well as series from s.to. It runs on Windows, macOS, and Linux, providing a seamless experience for offline viewing or instant playback.

![GitHub Release](https://img.shields.io/github/v/release/phoenixthrush/AniWorld-Downloader)
[![PyPI Downloads](https://static.pepy.tech/badge/aniworld)](https://pepy.tech/projects/aniworld)
![PyPI - Downloads](https://img.shields.io/pypi/dm/aniworld)
![GitHub License](https://img.shields.io/github/license/phoenixthrush/AniWorld-Downloader)
![GitHub Issues or Pull Requests](https://img.shields.io/github/issues/phoenixthrush/AniWorld-Downloader)
![GitHub Repo stars](https://img.shields.io/github/stars/phoenixthrush/AniWorld-Downloader)
![GitHub forks](https://img.shields.io/github/forks/phoenixthrush/AniWorld-Downloader)

![AniWorld Downloader - Demo](https://github.com/phoenixthrush/AniWorld-Downloader/blob/next/.github/assets/demo.png?raw=true)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## TL;DR - Quick Start

```text
# Installation
pip install --upgrade git+https://github.com/phoenixthrush/AniWorld-Downloader.git@models#egg=aniworld

# Usage
aniworld
```

> **Note:**
> The above command installs the latest development version instead of the stable release. If you want to install the latest stable version, simply run `pip install -U aniworld`.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Still in Development from v3

- [ ] Implement arguments: aniskip and keep-watching
- [ ] README -> add sections from v3
- [ ] Nuitka -> fix build crash
- [ ] Remove empty lines below action when running on docker run -it
- [ ] Detect docker environment to omit adding env variables when running in docker run -it
- [ ] WebUI -> coming soon

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Features

- Downloading: Grab full series, seasons, or individual episodes for offline viewing.
- Streaming: Watch episodes immediately with the built-in mpv or syncplay player.
- Auto-Next Playback: Seamlessly move to the next episode without interruption.
- Multiple Providers: Stream from a variety of sources on aniworld.to and s.to.
- Language Preferences: Switch effortlessly between German Dub, English Sub, or German Sub.
- Muxing: Automatically combine video and audio streams into a single file.
- AniSkip Integration: Automatically skip intros and outros for a smoother experience.
- Group Watching: Sync anime sessions with friends via Syncplay.
- Web Interface: Browse, download, and manage your anime queue with a modern web UI.
- Docker Ready: Easily deploy using Docker or Docker Compose.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Working Providers

> They are currently extremely unstable and will be worked on.
> The focus currently lies on
> aniworld: VOE, Filemoon, Vidmoly
> serienstream: VOE, Vidoza

- [x] Doodstream
- [ ] Filemoon
- [ ] Hanime
- [ ] LoadX
- [ ] Luluvdo
- [ ] SpeedFiles
- [ ] Streamtape
- [x] Vidoza
- [x] Vidmoly
- [x] VOE

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Docker

```bash
docker build -t aniworld .
```

- **macOS/Linux (bash/zsh):**

  ```bash
  docker run -it --rm \
    -v "${PWD}/Downloads:/app/Downloads" \
    -e ANIWORLD_DOCKER=1 \
    -e ANIWORLD_DOWNLOAD_PATH="/app/Downloads" \
    aniworld python -m aniworld
  ```

- **Windows (PowerShell):**

  ```powershell
  docker run -it --rm `
    -v "${PWD}\Downloads:/app/Downloads" `
    -e ANIWORLD_DOCKER=1 `
    -e ANIWORLD_DOWNLOAD_PATH="/app/Downloads" `
    aniworld python -m aniworld
  ```

- **Windows (CMD):**

  ```cmd
  docker run -it --rm ^
    -v "%cd%\Downloads:/app/Downloads" ^
    -e ANIWORLD_DOCKER=1 ^
    -e ANIWORLD_DOWNLOAD_PATH="/app/Downloads" ^
    aniworld python -m aniworld
  ```

> **Note:**
> Set `ANIWORLD_DOCKER=1` and `ANIWORLD_DOWNLOAD_PATH="/app/Downloads"` when running in Docker to ensure downloads are placed in the mounted folder. If you do not mount the Downloads directory, files created in the container will not persist on your host system.
> Environment variables will be replaced by a config file internally in the future.

### Docker Compose

```bash
docker-compose up -d --build
```

> This currently just serves the Downloads folder over HTTP on port 8080 until the real web UI is implemented. You can access it at <http://localhost:8080>.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Contributing

Contributions to AniWorld Downloader are highly appreciated! You can help enhance the project by:

- **Reporting Bugs**: Identify and report issues to improve functionality
- **Suggesting Features**: Share ideas to expand the tool's capabilities
- **Submitting Pull Requests**: Contribute code to fix bugs or add new features
- **Improving Documentation**: Help enhance user guides and technical documentation

### Contributors

<a href="https://github.com/phoenixthrush/AniWorld-Downloader/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=phoenixthrush/AniWorld-Downloader" alt="Contributors" />
</a>

- **Lulu** (since Sep 14, 2024)  
  [![wakatime](https://wakatime.com/badge/user/ebc8f6ad-7a1c-4f3a-ad43-cc402feab5fc/project/f39b2952-8865-4176-8ccc-4716e73d0df3.svg)](https://wakatime.com/badge/user/ebc8f6ad-7a1c-4f3a-ad43-cc402feab5fc/project/f39b2952-8865-4176-8ccc-4716e73d0df3)

- **Tmaster055** (since Oct 21, 2024)  
  [![Wakatime Badge](https://wakatime.com/badge/user/79a1926c-65a1-4f1c-baf3-368712ebbf97/project/5f191c34-1ee2-4850-95c3-8d85d516c449.svg)](https://wakatime.com/badge/user/79a1926c-65a1-4f1c-baf3-368712ebbf97/project/5f191c34-1ee2-4850-95c3-8d85d516c449.svg)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Documentation

For comprehensive user guides, tutorials, and additional documentation, visit the official documentation website:
[AniWorld-Downloader-Docs](https://www.phoenixthrush.com/AniWorld-Downloader-Docs/)

The documentation is continuously updated with new features, detailed tutorials, and troubleshooting guides to help you get the most out of AniWorld Downloader.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Dependencies

- **niquests** – For making HTTP requests
- **npyscreen** – For building text-based user interfaces
- **ffmpeg-python** – For handling multimedia processing
- **python-dotenv** – For managing environment variables
- **fake-useragent** – For generating random user agents

Windows only dependencies:

- **windows-curses** – For enabling curses support on Windows

All required dependencies are installed automatically when AniWorld Downloader is installed via `pip`.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Credits

AniWorld Downloader is built upon the work of several amazing open-source projects:

- **[mpv](https://github.com/mpv-player/mpv.git)**: A versatile media player used for seamless streaming
- **[Syncplay](https://github.com/Syncplay/syncplay.git)**: Enables synchronized playback sessions with friends
- **[Anime4K](https://github.com/bloc97/Anime4K)**: A cutting-edge real-time upscaler for enhancing anime video quality
- **[Aniskip](https://api.aniskip.com/api-docs)**: Provides the opening and ending skip times for the Aniskip extension

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Support

If you need help with AniWorld Downloader, you can:

- **Submit an issue** on the [GitHub Issues](https://github.com/phoenixthrush/AniWorld-Downloader/issues) page
- **Reach out directly** via email at [contact@phoenixthrush.com](mailto:contact@phoenixthrush.com) or on Discord at `phoenixthrush` or `tmaster067`

While email support is available, opening a GitHub issue is preferred, even for installation-related questions, as it helps others benefit from shared solutions. However, feel free to email if that's your preference.

If you find AniWorld Downloader useful, consider starring the repository on GitHub. Your support is greatly appreciated and inspires continued development.

Thank you for using AniWorld Downloader!

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Legal Disclaimer

AniWorld Downloader is a client-side tool that helps you access content hosted by third-party websites. It does not host, upload, store, or distribute any media itself.

AniWorld Downloader is not intended to promote piracy or copyright infringement. You are solely responsible for how you use the software and for ensuring that your use complies with applicable laws and the terms of the websites you access.

The developer provides this project “as is” and is not responsible for third-party content, external links, or the availability, accuracy, legality, or reliability of any third-party service.

If you have concerns about specific content, please contact the relevant website owner, administrator, or hosting provider.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=phoenixthrush/AniWorld-Downloader&type=Date)](https://star-history.com/#phoenixthrush/AniWorld-Downloader&Date)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## License

This project is licensed under the **[MIT License](LICENSE)**.
For more details, see the LICENSE file.
