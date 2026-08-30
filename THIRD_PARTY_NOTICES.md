# Third-party notices

This project orchestrates or uses the following third-party software. Each component remains subject to its own license and trademark terms.

| Component | Purpose | License / source |
|---|---|---|
| Ghost | Content management system, pulled as the official container image | MIT — https://github.com/TryGhost/Ghost/blob/main/LICENSE |
| MySQL Community Server | Database, pulled as the official container image | GPL-2.0 — https://github.com/docker-library/mysql |
| Docker CLI | Container management inside the QNAP manager image | Apache-2.0 — https://github.com/docker/cli/blob/master/LICENSE |
| Flask | Web interface framework | BSD-3-Clause — https://github.com/pallets/flask/blob/main/LICENSE.txt |
| Alpine Linux | Base operating system and packages | Component-specific open-source licenses — https://www.alpinelinux.org/about/ |
| Node.js | Runtime for the optional Ghost publishing client | MIT and bundled third-party licenses — https://github.com/nodejs/node/blob/main/LICENSE |
| @tryghost/admin-api | Optional Ghost Admin API client | See the package and its included license — https://www.npmjs.com/package/@tryghost/admin-api |

The project does not modify or relicense Ghost or MySQL. Their official images are pulled separately at installation or update time. Copyright notices and license files included in upstream images and packages must not be removed.

Ghost, QNAP, Docker, MySQL, Oracle and other names or marks belong to their respective owners. Their use in this project is descriptive and does not imply sponsorship, certification or endorsement.
