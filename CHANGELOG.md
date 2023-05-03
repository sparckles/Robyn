# Changelog

## [Unreleased](https://github.com/sansyrox/robyn/tree/HEAD)

[Full Changelog](https://github.com/sansyrox/robyn/compare/v0.26.1...HEAD)

**Closed issues:**

- Payload reached size limit. [\#463](https://github.com/sansyrox/robyn/issues/463)
- Proposal to rename `params` with `path_params` [\#457](https://github.com/sansyrox/robyn/issues/457)

**Merged pull requests:**

- feat: allow configurable payload sizes [\#465](https://github.com/sansyrox/robyn/pull/465) ([sansyrox](https://github.com/sansyrox))
- docs: remove test pypi instructions from pr template [\#462](https://github.com/sansyrox/robyn/pull/462) ([sansyrox](https://github.com/sansyrox))
- Rename params with path\_params [\#460](https://github.com/sansyrox/robyn/pull/460) ([carlosm27](https://github.com/carlosm27))
- feat: Implement global CORS [\#458](https://github.com/sansyrox/robyn/pull/458) ([sansyrox](https://github.com/sansyrox))

## [v0.26.1](https://github.com/sansyrox/robyn/tree/v0.26.1) (2023-04-05)

[Full Changelog](https://github.com/sansyrox/robyn/compare/v0.26.0...v0.26.1)

**Fixed bugs:**

- Can't access new or updated route while on dev option [\#439](https://github.com/sansyrox/robyn/issues/439)

**Closed issues:**

- Add documentation for `robyn.env` file [\#454](https://github.com/sansyrox/robyn/issues/454)

**Merged pull requests:**

- Release v0.26.1 [\#461](https://github.com/sansyrox/robyn/pull/461) ([sansyrox](https://github.com/sansyrox))
- \[pre-commit.ci\] pre-commit autoupdate [\#459](https://github.com/sansyrox/robyn/pull/459) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#452](https://github.com/sansyrox/robyn/pull/452) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- docs: Add docs for v0.26.0 [\#451](https://github.com/sansyrox/robyn/pull/451) ([sansyrox](https://github.com/sansyrox))
- fix\(dev\): fix hot reloading with dev flag [\#446](https://github.com/sansyrox/robyn/pull/446) ([AntoineRR](https://github.com/AntoineRR))

## [v0.26.0](https://github.com/sansyrox/robyn/tree/v0.26.0) (2023-03-24)

[Full Changelog](https://github.com/sansyrox/robyn/compare/v0.25.0...v0.26.0)

**Implemented enhancements:**

- \[Feature Request\] Robyn providing Status Codes? [\#423](https://github.com/sansyrox/robyn/issues/423)
- \[Feature Request\] Allow global level Response headers [\#335](https://github.com/sansyrox/robyn/issues/335)

**Fixed bugs:**

- \[BUG\] `uvloop` ModuleNotFoundError: No module named 'uvloop' on Ubuntu Docker Image [\#395](https://github.com/sansyrox/robyn/issues/395)

**Closed issues:**

- \[Feature Request\] When Robyn can have a middleware mechanism like flask or django [\#350](https://github.com/sansyrox/robyn/issues/350)
- Forced shutdown locks console. \[BUG\] [\#317](https://github.com/sansyrox/robyn/issues/317)

**Merged pull requests:**

- \[pre-commit.ci\] pre-commit autoupdate [\#449](https://github.com/sansyrox/robyn/pull/449) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- fix: Implement auto installation of uvloop on linux arm [\#445](https://github.com/sansyrox/robyn/pull/445) ([sansyrox](https://github.com/sansyrox))
- chore: update rust dependencies [\#444](https://github.com/sansyrox/robyn/pull/444) ([AntoineRR](https://github.com/AntoineRR))
- feat: Implement performance benchmarking [\#443](https://github.com/sansyrox/robyn/pull/443) ([sansyrox](https://github.com/sansyrox))
- feat: expose request/connection info [\#441](https://github.com/sansyrox/robyn/pull/441) ([r3b-fish](https://github.com/r3b-fish))
- Install the CodeSee workflow. [\#438](https://github.com/sansyrox/robyn/pull/438) ([codesee-maps[bot]](https://github.com/apps/codesee-maps))
- \[pre-commit.ci\] pre-commit autoupdate [\#437](https://github.com/sansyrox/robyn/pull/437) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Replace integer status codes with Enum values of StatusCodes [\#436](https://github.com/sansyrox/robyn/pull/436) ([Noborita9](https://github.com/Noborita9))
- added `star-history` [\#434](https://github.com/sansyrox/robyn/pull/434) ([hemangjoshi37a](https://github.com/hemangjoshi37a))
- \[pre-commit.ci\] pre-commit autoupdate [\#433](https://github.com/sansyrox/robyn/pull/433) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- feat: Robyn providing status codes [\#429](https://github.com/sansyrox/robyn/pull/429) ([carlosm27](https://github.com/carlosm27))
- feat: Allow global level Response headers [\#410](https://github.com/sansyrox/robyn/pull/410) ([ParthS007](https://github.com/ParthS007))
- feat: get rid of intermediate representations of requests and responses [\#397](https://github.com/sansyrox/robyn/pull/397) ([AntoineRR](https://github.com/AntoineRR))

## [v0.25.0](https://github.com/sansyrox/robyn/tree/v0.25.0) (2023-02-20)

[Full Changelog](https://github.com/sansyrox/robyn/compare/v0.24.1...v0.25.0)

**Implemented enhancements:**

- using robyn with some frameworks [\#420](https://github.com/sansyrox/robyn/issues/420)

**Fixed bugs:**

- Template Rendering is not working in some browsers [\#426](https://github.com/sansyrox/robyn/issues/426)

**Closed issues:**

- \[Feature Request\] Show support for Python versions in the README [\#396](https://github.com/sansyrox/robyn/issues/396)
- \[BUG\] The dev flag doesn't set the log level to DEBUG [\#385](https://github.com/sansyrox/robyn/issues/385)
- \[BUG\] All tests are not passing on windows [\#372](https://github.com/sansyrox/robyn/issues/372)
- \[Feature Request\] Add  views/view controllers [\#221](https://github.com/sansyrox/robyn/issues/221)

**Merged pull requests:**

- fix: Add proper headers to the templates return types [\#427](https://github.com/sansyrox/robyn/pull/427) ([sansyrox](https://github.com/sansyrox))
- \[pre-commit.ci\] pre-commit autoupdate [\#425](https://github.com/sansyrox/robyn/pull/425) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- docs: Add documentation for views [\#424](https://github.com/sansyrox/robyn/pull/424) ([sansyrox](https://github.com/sansyrox))
- better way to compare type [\#421](https://github.com/sansyrox/robyn/pull/421) ([jmishra01](https://github.com/jmishra01))
- style\(landing\_page\): fix the style of github logo on the landing page [\#419](https://github.com/sansyrox/robyn/pull/419) ([sansyrox](https://github.com/sansyrox))
- docs: improve readme [\#418](https://github.com/sansyrox/robyn/pull/418) ([AntoineRR](https://github.com/AntoineRR))
- docs: add dark mode to website [\#416](https://github.com/sansyrox/robyn/pull/416) ([AntoineRR](https://github.com/AntoineRR))
- chore: improve issue templates [\#413](https://github.com/sansyrox/robyn/pull/413) ([AntoineRR](https://github.com/AntoineRR))
- \[pre-commit.ci\] pre-commit autoupdate [\#412](https://github.com/sansyrox/robyn/pull/412) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- fix: fixed CONTRIBUTE.md link into docs/README.md file, changing it f… [\#411](https://github.com/sansyrox/robyn/pull/411) ([Kop3sh](https://github.com/Kop3sh))
- chore\(ci\): fix rust ci warnings [\#408](https://github.com/sansyrox/robyn/pull/408) ([AntoineRR](https://github.com/AntoineRR))
- feat: Add view controllers [\#407](https://github.com/sansyrox/robyn/pull/407) ([mikaeelghr](https://github.com/mikaeelghr))
- Fix docs: support version [\#404](https://github.com/sansyrox/robyn/pull/404) ([Oluwaseun241](https://github.com/Oluwaseun241))
- fix: Fix Windows tests [\#402](https://github.com/sansyrox/robyn/pull/402) ([sansyrox](https://github.com/sansyrox))
- docs: Update PyPi metadata [\#401](https://github.com/sansyrox/robyn/pull/401) ([sansyrox](https://github.com/sansyrox))
- fix\(test\): fix tests on windows [\#400](https://github.com/sansyrox/robyn/pull/400) ([AntoineRR](https://github.com/AntoineRR))
- fix: various improvements around the dev flag [\#388](https://github.com/sansyrox/robyn/pull/388) ([AntoineRR](https://github.com/AntoineRR))

## [v0.24.1](https://github.com/sansyrox/robyn/tree/v0.24.1) (2023-02-09)

[Full Changelog](https://github.com/sansyrox/robyn/compare/v0.24.0...v0.24.1)

**Closed issues:**

- \[BUG\] \[Windows\] Terminal hanging after Ctrl+C is pressed on Robyn server [\#373](https://github.com/sansyrox/robyn/issues/373)

**Merged pull requests:**

- \[pre-commit.ci\] pre-commit autoupdate [\#394](https://github.com/sansyrox/robyn/pull/394) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- docs: add documentation regarding byte response [\#392](https://github.com/sansyrox/robyn/pull/392) ([sansyrox](https://github.com/sansyrox))
- fix: fix terminal hijacking in windows [\#391](https://github.com/sansyrox/robyn/pull/391) ([sansyrox](https://github.com/sansyrox))
- chore: fix requirements files and update packages [\#389](https://github.com/sansyrox/robyn/pull/389) ([AntoineRR](https://github.com/AntoineRR))
- small correction in docs [\#387](https://github.com/sansyrox/robyn/pull/387) ([tkanhe](https://github.com/tkanhe))
- \[pre-commit.ci\] pre-commit autoupdate [\#384](https://github.com/sansyrox/robyn/pull/384) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- ci: build artifacts on every push and pull [\#378](https://github.com/sansyrox/robyn/pull/378) ([sansyrox](https://github.com/sansyrox))
- test: organize and add tests [\#377](https://github.com/sansyrox/robyn/pull/377) ([AntoineRR](https://github.com/AntoineRR))
- Changed Response to use body: bytes [\#375](https://github.com/sansyrox/robyn/pull/375) ([madhavajay](https://github.com/madhavajay))

## [v0.24.0](https://github.com/sansyrox/robyn/tree/v0.24.0) (2023-02-06)

[Full Changelog](https://github.com/sansyrox/robyn/compare/v0.23.1...v0.24.0)

**Closed issues:**

- \[BUG\] Release builds are not working [\#386](https://github.com/sansyrox/robyn/issues/386)
- \[BUG\] Can't send raw bytes [\#374](https://github.com/sansyrox/robyn/issues/374)

## [v0.23.1](https://github.com/sansyrox/robyn/tree/v0.23.1) (2023-01-30)

[Full Changelog](https://github.com/sansyrox/robyn/compare/v0.23.0...v0.23.1)

**Closed issues:**

- \[BUG\] Return 500 status code when route is raising [\#381](https://github.com/sansyrox/robyn/issues/381)
- \[BUG\] Return 404 status code when route isn't set [\#376](https://github.com/sansyrox/robyn/issues/376)
- Add Appwrite as a sponsor in the README [\#348](https://github.com/sansyrox/robyn/issues/348)
- \[BUG\] Get Stared failed on Windows [\#340](https://github.com/sansyrox/robyn/issues/340)
- \[BUG\] Fix CI/CD pipeline [\#310](https://github.com/sansyrox/robyn/issues/310)

**Merged pull requests:**

- chore\(ci\): fix robyn installation in test CI [\#383](https://github.com/sansyrox/robyn/pull/383) ([AntoineRR](https://github.com/AntoineRR))
- fix: return 500 status code when route raise [\#382](https://github.com/sansyrox/robyn/pull/382) ([AntoineRR](https://github.com/AntoineRR))
- fix: return 404 status code when route isn't found [\#380](https://github.com/sansyrox/robyn/pull/380) ([AntoineRR](https://github.com/AntoineRR))
- ci: enable precommit hooks on everything [\#371](https://github.com/sansyrox/robyn/pull/371) ([sansyrox](https://github.com/sansyrox))
- chore: run tests on linux, macos and windows and release builds on ta… [\#370](https://github.com/sansyrox/robyn/pull/370) ([AntoineRR](https://github.com/AntoineRR))
- docs: add appwrite logo as sponsors [\#369](https://github.com/sansyrox/robyn/pull/369) ([sansyrox](https://github.com/sansyrox))
- test: improve pytest fixtures [\#368](https://github.com/sansyrox/robyn/pull/368) ([AntoineRR](https://github.com/AntoineRR))
- Move pre-commit hooks to use Ruff [\#364](https://github.com/sansyrox/robyn/pull/364) ([patrick91](https://github.com/patrick91))

## [v0.23.0](https://github.com/sansyrox/robyn/tree/v0.23.0) (2023-01-21)

[Full Changelog](https://github.com/sansyrox/robyn/compare/v0.22.1...v0.23.0)

**Closed issues:**

- \[Feature Request\] Improve the release and testing pipeline [\#341](https://github.com/sansyrox/robyn/issues/341)

**Merged pull requests:**

- ci: delete the test pypi workflow  [\#367](https://github.com/sansyrox/robyn/pull/367) ([sansyrox](https://github.com/sansyrox))
- docs: Add page icon to index page [\#365](https://github.com/sansyrox/robyn/pull/365) ([Abdur-rahmaanJ](https://github.com/Abdur-rahmaanJ))
- test: speed up tests [\#362](https://github.com/sansyrox/robyn/pull/362) ([AntoineRR](https://github.com/AntoineRR))
- Replace the default port with 8080 [\#352](https://github.com/sansyrox/robyn/pull/352) ([sansyrox](https://github.com/sansyrox))

## [v0.22.1](https://github.com/sansyrox/robyn/tree/v0.22.1) (2023-01-16)

[Full Changelog](https://github.com/sansyrox/robyn/compare/v0.22.0...v0.22.1)

**Closed issues:**

- \[BUG\] Python 3.11 error: metadata-generation-failed [\#357](https://github.com/sansyrox/robyn/issues/357)

**Merged pull requests:**

- ci: update precommit config [\#361](https://github.com/sansyrox/robyn/pull/361) ([sansyrox](https://github.com/sansyrox))
- \[pre-commit.ci\] pre-commit autoupdate [\#359](https://github.com/sansyrox/robyn/pull/359) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- chore\(ci\): add python 3.11 to the build and test CI [\#358](https://github.com/sansyrox/robyn/pull/358) ([AntoineRR](https://github.com/AntoineRR))
- Updates prose to format code block and docs [\#356](https://github.com/sansyrox/robyn/pull/356) ([rachfop](https://github.com/rachfop))

## [v0.22.0](https://github.com/sansyrox/robyn/tree/v0.22.0) (2023-01-14)

[Full Changelog](https://github.com/sansyrox/robyn/compare/v0.21.0...v0.22.0)

**Closed issues:**

- AttributeError: 'Robyn' object has no attribute 'headers'\[BUG\] [\#353](https://github.com/sansyrox/robyn/issues/353)
- \[Feature Request\] Allow support for multiple file types [\#344](https://github.com/sansyrox/robyn/issues/344)
- \[Feature Request\] Investigate if we need an unit tests for Python functions created in Rust [\#311](https://github.com/sansyrox/robyn/issues/311)
- \[Experimental Feature Request\] Story driven programming [\#258](https://github.com/sansyrox/robyn/issues/258)

**Merged pull requests:**

- fix: windows support [\#354](https://github.com/sansyrox/robyn/pull/354) ([sansyrox](https://github.com/sansyrox))
- fix: better handling of route return type [\#349](https://github.com/sansyrox/robyn/pull/349) ([AntoineRR](https://github.com/AntoineRR))

## [v0.21.0](https://github.com/sansyrox/robyn/tree/v0.21.0) (2023-01-06)

[Full Changelog](https://github.com/sansyrox/robyn/compare/v0.20.0...v0.21.0)

**Closed issues:**

- \[Feature Request\] Support for image file type [\#343](https://github.com/sansyrox/robyn/issues/343)
- Not able to see the added logs  [\#342](https://github.com/sansyrox/robyn/issues/342)
- \[Feature Request\] Hope robyn can support returning f-string format [\#338](https://github.com/sansyrox/robyn/issues/338)
- \[Feature Request\] Refactor Robyn response to allow objects other than strings [\#336](https://github.com/sansyrox/robyn/issues/336)
- \[BUG\] Custom headers not sent when const=False [\#323](https://github.com/sansyrox/robyn/issues/323)
- \[Feature Request\] Add documentation for custom template support in v0.19.0 [\#321](https://github.com/sansyrox/robyn/issues/321)
- \[BUG\] Always need to return a string in a route [\#305](https://github.com/sansyrox/robyn/issues/305)

**Merged pull requests:**

- fix: fix the static file serving [\#347](https://github.com/sansyrox/robyn/pull/347) ([sansyrox](https://github.com/sansyrox))
- feat: return Response from routes [\#346](https://github.com/sansyrox/robyn/pull/346) ([AntoineRR](https://github.com/AntoineRR))

## [v0.20.0](https://github.com/sansyrox/robyn/tree/v0.20.0) (2022-12-20)

[Full Changelog](https://github.com/sansyrox/robyn/compare/v0.19.2...v0.20.0)

**Closed issues:**

- \[Feature Request\] Add an automated benchmark script [\#320](https://github.com/sansyrox/robyn/issues/320)

**Merged pull requests:**

- feat: allow non string types in response [\#337](https://github.com/sansyrox/robyn/pull/337) ([sansyrox](https://github.com/sansyrox))
- feat: add an auto benchmark script [\#329](https://github.com/sansyrox/robyn/pull/329) ([AntoineRR](https://github.com/AntoineRR))

## [v0.19.2](https://github.com/sansyrox/robyn/tree/v0.19.2) (2022-12-14)

[Full Changelog](https://github.com/sansyrox/robyn/compare/v0.19.1...v0.19.2)

**Closed issues:**

- \[BUG\] The --dev flag not working on Ubuntu 20.04 [\#332](https://github.com/sansyrox/robyn/issues/332)
- \[Feature Request\] Allow the ability of sending the headers from the same route [\#325](https://github.com/sansyrox/robyn/issues/325)

**Merged pull requests:**

- fix: allow response headers  and fix headers not working in const requests [\#331](https://github.com/sansyrox/robyn/pull/331) ([sansyrox](https://github.com/sansyrox))
- fix: factorizing code [\#322](https://github.com/sansyrox/robyn/pull/322) ([AntoineRR](https://github.com/AntoineRR))

## [v0.19.1](https://github.com/sansyrox/robyn/tree/v0.19.1) (2022-12-03)

[Full Changelog](https://github.com/sansyrox/robyn/compare/v0.19.0...v0.19.1)

## [v0.19.0](https://github.com/sansyrox/robyn/tree/v0.19.0) (2022-12-02)

[Full Changelog](https://github.com/sansyrox/robyn/compare/v0.18.3...v0.19.0)

**Closed issues:**

- \[Feature Request\] Allow the ability of sending the headers from the same route [\#326](https://github.com/sansyrox/robyn/issues/326)
- \[Feature Request\] Allow the ability of sending the headers from the same route [\#324](https://github.com/sansyrox/robyn/issues/324)
- \[BUG\] Error in Examples section in Documentation [\#314](https://github.com/sansyrox/robyn/issues/314)
- \[BUG\] Wrong link for the blog post on Robyn [\#306](https://github.com/sansyrox/robyn/issues/306)
- Add documentation about deployment [\#93](https://github.com/sansyrox/robyn/issues/93)
- Add support for templates! [\#10](https://github.com/sansyrox/robyn/issues/10)

**Merged pull requests:**

- docs: update hosting docs [\#319](https://github.com/sansyrox/robyn/pull/319) ([sansyrox](https://github.com/sansyrox))
- Various improvements around the index method [\#318](https://github.com/sansyrox/robyn/pull/318) ([AntoineRR](https://github.com/AntoineRR))
- Add  Railway deployment process.  [\#316](https://github.com/sansyrox/robyn/pull/316) ([carlosm27](https://github.com/carlosm27))
- docs: fix middleware section in examples [\#315](https://github.com/sansyrox/robyn/pull/315) ([sansyrox](https://github.com/sansyrox))
- docs: fix blog link in website [\#309](https://github.com/sansyrox/robyn/pull/309) ([sansyrox](https://github.com/sansyrox))
- Router refactor [\#307](https://github.com/sansyrox/robyn/pull/307) ([AntoineRR](https://github.com/AntoineRR))

## [v0.18.3](https://github.com/sansyrox/robyn/tree/v0.18.3) (2022-11-10)

[Full Changelog](https://github.com/sansyrox/robyn/compare/v0.18.2...v0.18.3)

**Closed issues:**

- \[BUG\] `--log-level` not working [\#300](https://github.com/sansyrox/robyn/issues/300)
- \[Feature Request\] Refactor Code to include better types [\#254](https://github.com/sansyrox/robyn/issues/254)

**Merged pull requests:**

- fix: log level not working [\#303](https://github.com/sansyrox/robyn/pull/303) ([sansyrox](https://github.com/sansyrox))
- add route type enum [\#299](https://github.com/sansyrox/robyn/pull/299) ([suhailmalik07](https://github.com/suhailmalik07))

## [v0.18.2](https://github.com/sansyrox/robyn/tree/v0.18.2) (2022-11-05)

[Full Changelog](https://github.com/sansyrox/robyn/compare/v0.18.1...v0.18.2)

**Closed issues:**

- \[Feature Request?\] Update `matchit` crate to the most recent version [\#291](https://github.com/sansyrox/robyn/issues/291)
- \[Feature Request\] Add `@wraps` in route dectorators [\#285](https://github.com/sansyrox/robyn/issues/285)
- \[Feature Request\] fix clippy issues [\#265](https://github.com/sansyrox/robyn/issues/265)

**Merged pull requests:**

- style: add logging for url port and host [\#304](https://github.com/sansyrox/robyn/pull/304) ([sansyrox](https://github.com/sansyrox))
- fix config of port and url [\#302](https://github.com/sansyrox/robyn/pull/302) ([kimhyun5u](https://github.com/kimhyun5u))
- update rust packages to latest [\#298](https://github.com/sansyrox/robyn/pull/298) ([suhailmalik07](https://github.com/suhailmalik07))
- fix: retain metadata of the route functions [\#295](https://github.com/sansyrox/robyn/pull/295) ([sansyrox](https://github.com/sansyrox))
- `SocketHeld::new` refactor [\#294](https://github.com/sansyrox/robyn/pull/294) ([Jamyw7g](https://github.com/Jamyw7g))

## [v0.18.1](https://github.com/sansyrox/robyn/tree/v0.18.1) (2022-10-23)

[Full Changelog](https://github.com/sansyrox/robyn/compare/v0.18.0...v0.18.1)

**Merged pull requests:**

- fix: replaced match with if let [\#293](https://github.com/sansyrox/robyn/pull/293) ([Markaeus](https://github.com/Markaeus))
-  Hotfix detecting robyn.env [\#292](https://github.com/sansyrox/robyn/pull/292) ([Shending-Help](https://github.com/Shending-Help))
- fix: enable hot reload on windows [\#290](https://github.com/sansyrox/robyn/pull/290) ([guilefoylegaurav](https://github.com/guilefoylegaurav))

## [v0.18.0](https://github.com/sansyrox/robyn/tree/v0.18.0) (2022-10-12)

[Full Changelog](https://github.com/sansyrox/robyn/compare/v0.17.5...v0.18.0)

**Closed issues:**

- \[BUG\] The --dev mode spawns more servers without clearing previous ones. [\#249](https://github.com/sansyrox/robyn/issues/249)
- \[Feature\] Add support for Env variables and a robyn.yaml config file [\#97](https://github.com/sansyrox/robyn/issues/97)

**Merged pull requests:**

- testing env support [\#288](https://github.com/sansyrox/robyn/pull/288) ([Shending-Help](https://github.com/Shending-Help))
- Feature add support for env variables [\#286](https://github.com/sansyrox/robyn/pull/286) ([Shending-Help](https://github.com/Shending-Help))
- fix: add proper kill process to conftest. \#249 [\#278](https://github.com/sansyrox/robyn/pull/278) ([guilefoylegaurav](https://github.com/guilefoylegaurav))

## [v0.17.5](https://github.com/sansyrox/robyn/tree/v0.17.5) (2022-09-14)

[Full Changelog](https://github.com/sansyrox/robyn/compare/v0.17.4...v0.17.5)

**Closed issues:**

- \[BUG\] README.md Discord link is invalid [\#272](https://github.com/sansyrox/robyn/issues/272)
- \[Feature Request\] Add Digital Ocean to list of sponsors in Robyn Docs [\#270](https://github.com/sansyrox/robyn/issues/270)
- \[Feature Request\] Add PyCon USA lightning talk in resources section [\#204](https://github.com/sansyrox/robyn/issues/204)
- \[Feature Request\] Add community/ resources section in Docs or README  [\#203](https://github.com/sansyrox/robyn/issues/203)
- \[Feature Request\] Update the new architecture on the docs website [\#191](https://github.com/sansyrox/robyn/issues/191)
- Add examples section [\#101](https://github.com/sansyrox/robyn/issues/101)

**Merged pull requests:**

- Don't run sync functions in pool [\#282](https://github.com/sansyrox/robyn/pull/282) ([JackThomson2](https://github.com/JackThomson2))
- Add documentation of Adding GraphQL support | version 1 [\#275](https://github.com/sansyrox/robyn/pull/275) ([sansyrox](https://github.com/sansyrox))
- docs: improve documentation [\#269](https://github.com/sansyrox/robyn/pull/269) ([sansyrox](https://github.com/sansyrox))

## [v0.17.4](https://github.com/sansyrox/robyn/tree/v0.17.4) (2022-08-25)

[Full Changelog](https://github.com/sansyrox/robyn/compare/v0.17.3...v0.17.4)

**Closed issues:**

- \[BUG?\] Startup failure OSError: \[WinError 87\] The parameter is incorrect [\#252](https://github.com/sansyrox/robyn/issues/252)
- \[Feature Request\] Add mypy for pyi\(stubs\) synchronisation [\#226](https://github.com/sansyrox/robyn/issues/226)
- not working on mac/windows [\#140](https://github.com/sansyrox/robyn/issues/140)

**Merged pull requests:**

- Father, forgive me, for I am adding inline types. [\#266](https://github.com/sansyrox/robyn/pull/266) ([sansyrox](https://github.com/sansyrox))

## [v0.17.3](https://github.com/sansyrox/robyn/tree/v0.17.3) (2022-08-17)

[Full Changelog](https://github.com/sansyrox/robyn/compare/v0.17.2...v0.17.3)

**Merged pull requests:**

- fix: parse int status code to str [\#264](https://github.com/sansyrox/robyn/pull/264) ([hougesen](https://github.com/hougesen))

## [v0.17.2](https://github.com/sansyrox/robyn/tree/v0.17.2) (2022-08-11)

[Full Changelog](https://github.com/sansyrox/robyn/compare/v0.17.1...v0.17.2)

**Fixed bugs:**

- Cannot run Robyn on Windows [\#139](https://github.com/sansyrox/robyn/issues/139)

**Closed issues:**

- \[BUG\] Move away from circle ci [\#240](https://github.com/sansyrox/robyn/issues/240)
- Migrate the community to discord [\#239](https://github.com/sansyrox/robyn/issues/239)
- \[Feature Request\] Release on test pypi before releasing on the main PyPi [\#224](https://github.com/sansyrox/robyn/issues/224)
- For 0.8.x [\#75](https://github.com/sansyrox/robyn/issues/75)
- Add a layer of caching in front of router [\#59](https://github.com/sansyrox/robyn/issues/59)

**Merged pull requests:**

- Windows fix [\#261](https://github.com/sansyrox/robyn/pull/261) ([sansyrox](https://github.com/sansyrox))
- ci: enable fail fast for faster response time in the pipelines [\#260](https://github.com/sansyrox/robyn/pull/260) ([sansyrox](https://github.com/sansyrox))
- ci: add github actions to publish every PR on test pypi [\#259](https://github.com/sansyrox/robyn/pull/259) ([sansyrox](https://github.com/sansyrox))
- Fix typo in README [\#246](https://github.com/sansyrox/robyn/pull/246) ([bartbroere](https://github.com/bartbroere))
- chore\(ci\): move pytest from CircleCi to Github Actions [\#241](https://github.com/sansyrox/robyn/pull/241) ([AntoineRR](https://github.com/AntoineRR))

## [v0.17.1](https://github.com/sansyrox/robyn/tree/v0.17.1) (2022-07-19)

[Full Changelog](https://github.com/sansyrox/robyn/compare/v0.17.0...v0.17.1)

**Closed issues:**

- \[Feature Request\] add clippy in ci [\#236](https://github.com/sansyrox/robyn/issues/236)
- \[BUG\] Headers not available [\#231](https://github.com/sansyrox/robyn/issues/231)
- \[Feature Request\] Add an all contributor bot in the README of the repo [\#225](https://github.com/sansyrox/robyn/issues/225)

**Merged pull requests:**

- Add Rust CI [\#237](https://github.com/sansyrox/robyn/pull/237) ([AntoineRR](https://github.com/AntoineRR))
- Contributors added in Readme [\#235](https://github.com/sansyrox/robyn/pull/235) ([orvil1026](https://github.com/orvil1026))
- fix external project link in README [\#234](https://github.com/sansyrox/robyn/pull/234) ([touilleMan](https://github.com/touilleMan))
- fix: fix request headers not being propagated [\#232](https://github.com/sansyrox/robyn/pull/232) ([sansyrox](https://github.com/sansyrox))
- Upgrade GitHub Actions and add Python 3.10 [\#230](https://github.com/sansyrox/robyn/pull/230) ([cclauss](https://github.com/cclauss))
- OrbUp: Upgrade the CircleCI Orbs [\#229](https://github.com/sansyrox/robyn/pull/229) ([cclauss](https://github.com/cclauss))
- CHANGELOG.md: Fix typo [\#228](https://github.com/sansyrox/robyn/pull/228) ([cclauss](https://github.com/cclauss))

## [v0.17.0](https://github.com/sansyrox/robyn/tree/v0.17.0) (2022-07-06)

[Full Changelog](https://github.com/sansyrox/robyn/compare/v0.16.6...v0.17.0)

**Closed issues:**

- A refactor [\#176](https://github.com/sansyrox/robyn/issues/176)
- \[Proposal\] Const Requests [\#48](https://github.com/sansyrox/robyn/issues/48)

**Merged pull requests:**

- Add a const router [\#210](https://github.com/sansyrox/robyn/pull/210) ([sansyrox](https://github.com/sansyrox))

## [v0.16.6](https://github.com/sansyrox/robyn/tree/v0.16.6) (2022-07-02)

[Full Changelog](https://github.com/sansyrox/robyn/compare/v0.16.5...v0.16.6)

## [v0.16.5](https://github.com/sansyrox/robyn/tree/v0.16.5) (2022-07-01)

[Full Changelog](https://github.com/sansyrox/robyn/compare/v0.16.4...v0.16.5)

**Closed issues:**

- \[Feature Request\] Add sponsors in the repo and website [\#212](https://github.com/sansyrox/robyn/issues/212)
- \[Feature Request\] Add commitizen as a dev dependency [\#211](https://github.com/sansyrox/robyn/issues/211)
- Add better logging [\#158](https://github.com/sansyrox/robyn/issues/158)
- Remove freeport dependency [\#151](https://github.com/sansyrox/robyn/issues/151)
- Add websocket support [\#104](https://github.com/sansyrox/robyn/issues/104)
- Maintenance issue [\#56](https://github.com/sansyrox/robyn/issues/56)
- Improve Readme [\#4](https://github.com/sansyrox/robyn/issues/4)

**Merged pull requests:**

- fix: Fixes the crashing dev mode [\#218](https://github.com/sansyrox/robyn/pull/218) ([sansyrox](https://github.com/sansyrox))
- feat: add commitizen as a dev dependency [\#216](https://github.com/sansyrox/robyn/pull/216) ([sansyrox](https://github.com/sansyrox))
- Isort imports [\#205](https://github.com/sansyrox/robyn/pull/205) ([sansyrox](https://github.com/sansyrox))
- Add bridged logger. Improves performance substantially. [\#201](https://github.com/sansyrox/robyn/pull/201) ([sansyrox](https://github.com/sansyrox))
- Adds pre-commit hooks for black, flake8, isort [\#198](https://github.com/sansyrox/robyn/pull/198) ([chrismoradi](https://github.com/chrismoradi))
- Resolves port open issue when app is killed \#183 [\#196](https://github.com/sansyrox/robyn/pull/196) ([anandtripathi5](https://github.com/anandtripathi5))
- Removing unwraps [\#195](https://github.com/sansyrox/robyn/pull/195) ([sansyrox](https://github.com/sansyrox))

## [v0.16.4](https://github.com/sansyrox/robyn/tree/v0.16.4) (2022-05-30)

[Full Changelog](https://github.com/sansyrox/robyn/compare/v0.16.3...v0.16.4)

**Closed issues:**

- \[Feature Request\] Remove extra logs [\#200](https://github.com/sansyrox/robyn/issues/200)
- \[Feature Request\] Add precommit hook for black, flake8 and isort [\#194](https://github.com/sansyrox/robyn/issues/194)
- \[BUG\] Get rid of Hashmap Clones and Unwraps! [\#186](https://github.com/sansyrox/robyn/issues/186)

## [v0.16.3](https://github.com/sansyrox/robyn/tree/v0.16.3) (2022-05-18)

[Full Changelog](https://github.com/sansyrox/robyn/compare/v0.16.2...v0.16.3)

**Closed issues:**

- \[BUG\] Port not being free on app kill [\#183](https://github.com/sansyrox/robyn/issues/183)
- Build failure [\#166](https://github.com/sansyrox/robyn/issues/166)

## [v0.16.2](https://github.com/sansyrox/robyn/tree/v0.16.2) (2022-05-09)

[Full Changelog](https://github.com/sansyrox/robyn/compare/v0.16.1...v0.16.2)

## [v0.16.1](https://github.com/sansyrox/robyn/tree/v0.16.1) (2022-05-09)

[Full Changelog](https://github.com/sansyrox/robyn/compare/v0.16.0...v0.16.1)

**Closed issues:**

- Add Python stubs [\#130](https://github.com/sansyrox/robyn/issues/130)

**Merged pull requests:**

- Setup types for Robyn [\#192](https://github.com/sansyrox/robyn/pull/192) ([sansyrox](https://github.com/sansyrox))
- Fix build pipeline [\#190](https://github.com/sansyrox/robyn/pull/190) ([sansyrox](https://github.com/sansyrox))
- fix typo :pencil2: in api docs. [\#189](https://github.com/sansyrox/robyn/pull/189) ([sombralibre](https://github.com/sombralibre))
- Remove hashmap clones [\#187](https://github.com/sansyrox/robyn/pull/187) ([sansyrox](https://github.com/sansyrox))
- Code clean up | Modularise rust code [\#185](https://github.com/sansyrox/robyn/pull/185) ([sansyrox](https://github.com/sansyrox))
- Add experimental io-uring [\#184](https://github.com/sansyrox/robyn/pull/184) ([sansyrox](https://github.com/sansyrox))
- Implement Response headers [\#179](https://github.com/sansyrox/robyn/pull/179) ([sansyrox](https://github.com/sansyrox))
- Code cleanup [\#178](https://github.com/sansyrox/robyn/pull/178) ([sansyrox](https://github.com/sansyrox))

## [v0.16.0](https://github.com/sansyrox/robyn/tree/v0.16.0) (2022-04-29)

[Full Changelog](https://github.com/sansyrox/robyn/compare/v0.15.1...v0.16.0)

**Closed issues:**

- \[Feature Request\] Add list of sponsors on the project website  [\#182](https://github.com/sansyrox/robyn/issues/182)
- Optional build feature for io\_uring [\#177](https://github.com/sansyrox/robyn/issues/177)
- Create Custom headers for the response. [\#174](https://github.com/sansyrox/robyn/issues/174)

## [v0.15.1](https://github.com/sansyrox/robyn/tree/v0.15.1) (2022-03-24)

[Full Changelog](https://github.com/sansyrox/robyn/compare/v0.15.0...v0.15.1)

**Closed issues:**

- Add middleware support [\#95](https://github.com/sansyrox/robyn/issues/95)

**Merged pull requests:**

- Make websocket id accessible [\#173](https://github.com/sansyrox/robyn/pull/173) ([sansyrox](https://github.com/sansyrox))
- Use Clippy tool optimized code [\#171](https://github.com/sansyrox/robyn/pull/171) ([mrxiaozhuox](https://github.com/mrxiaozhuox))
- Modify headers [\#170](https://github.com/sansyrox/robyn/pull/170) ([sansyrox](https://github.com/sansyrox))
- Update README.md [\#168](https://github.com/sansyrox/robyn/pull/168) ([Polokghosh53](https://github.com/Polokghosh53))

## [v0.15.0](https://github.com/sansyrox/robyn/tree/v0.15.0) (2022-03-17)

[Full Changelog](https://github.com/sansyrox/robyn/compare/v0.14.0...v0.15.0)

**Closed issues:**

- \[BUG\] Unable to modify headers in middlewares [\#167](https://github.com/sansyrox/robyn/issues/167)
- Add Pycon talk link to docs [\#102](https://github.com/sansyrox/robyn/issues/102)

## [v0.14.0](https://github.com/sansyrox/robyn/tree/v0.14.0) (2022-03-03)

[Full Changelog](https://github.com/sansyrox/robyn/compare/v0.13.1...v0.14.0)

**Fixed bugs:**

- Build error [\#161](https://github.com/sansyrox/robyn/issues/161)

**Merged pull requests:**

- Implement Custom Response objects. [\#165](https://github.com/sansyrox/robyn/pull/165) ([sansyrox](https://github.com/sansyrox))
- Remove deprecated endpoints [\#162](https://github.com/sansyrox/robyn/pull/162) ([sansyrox](https://github.com/sansyrox))
- Fix: default url param in app.start [\#160](https://github.com/sansyrox/robyn/pull/160) ([sansyrox](https://github.com/sansyrox))
- Add middlewares [\#157](https://github.com/sansyrox/robyn/pull/157) ([sansyrox](https://github.com/sansyrox))
- Remove arc\(ing\) [\#156](https://github.com/sansyrox/robyn/pull/156) ([sansyrox](https://github.com/sansyrox))

## [v0.13.1](https://github.com/sansyrox/robyn/tree/v0.13.1) (2022-02-19)

[Full Changelog](https://github.com/sansyrox/robyn/compare/v0.13.0...v0.13.1)

## [v0.13.0](https://github.com/sansyrox/robyn/tree/v0.13.0) (2022-02-15)

[Full Changelog](https://github.com/sansyrox/robyn/compare/v0.12.1...v0.13.0)

## [v0.12.1](https://github.com/sansyrox/robyn/tree/v0.12.1) (2022-02-13)

[Full Changelog](https://github.com/sansyrox/robyn/compare/v0.12.0...v0.12.1)

**Closed issues:**

- \[BUG\] Default URL cannot be assigned [\#159](https://github.com/sansyrox/robyn/issues/159)
- Upcoming release\(s\) [\#141](https://github.com/sansyrox/robyn/issues/141)

## [v0.12.0](https://github.com/sansyrox/robyn/tree/v0.12.0) (2022-01-21)

[Full Changelog](https://github.com/sansyrox/robyn/compare/v0.11.1...v0.12.0)

**Closed issues:**

- Consider adding startup events [\#153](https://github.com/sansyrox/robyn/issues/153)
- Remove poetry dependency [\#150](https://github.com/sansyrox/robyn/issues/150)

**Merged pull requests:**

- Add Event handlers [\#154](https://github.com/sansyrox/robyn/pull/154) ([sansyrox](https://github.com/sansyrox))
- Remove poetry [\#152](https://github.com/sansyrox/robyn/pull/152) ([sansyrox](https://github.com/sansyrox))
- Use print instead of input after starting server [\#149](https://github.com/sansyrox/robyn/pull/149) ([klaa97](https://github.com/klaa97))
- Fix dev server [\#148](https://github.com/sansyrox/robyn/pull/148) ([sansyrox](https://github.com/sansyrox))
- URL queries [\#146](https://github.com/sansyrox/robyn/pull/146) ([patchgamestudio](https://github.com/patchgamestudio))
- Add project wide flake8 settings [\#143](https://github.com/sansyrox/robyn/pull/143) ([sansyrox](https://github.com/sansyrox))

## [v0.11.1](https://github.com/sansyrox/robyn/tree/v0.11.1) (2022-01-11)

[Full Changelog](https://github.com/sansyrox/robyn/compare/v0.11.0...v0.11.1)

## [v0.11.0](https://github.com/sansyrox/robyn/tree/v0.11.0) (2022-01-07)

[Full Changelog](https://github.com/sansyrox/robyn/compare/v0.10.0...v0.11.0)

**Fixed bugs:**

- Hot Reloading goes in an infinite loop [\#115](https://github.com/sansyrox/robyn/issues/115)

**Closed issues:**

- Benchmarks to Björn, uvicorn etc.  [\#142](https://github.com/sansyrox/robyn/issues/142)
- Add Python linter setup [\#129](https://github.com/sansyrox/robyn/issues/129)
- Add fixtures in testing [\#84](https://github.com/sansyrox/robyn/issues/84)

## [v0.10.0](https://github.com/sansyrox/robyn/tree/v0.10.0) (2021-12-20)

[Full Changelog](https://github.com/sansyrox/robyn/compare/v0.9.0...v0.10.0)

**Closed issues:**

- Add PyPI classifiers [\#127](https://github.com/sansyrox/robyn/issues/127)
- Robyn version 0.9.0 doesn't work on Mac M1 Models  [\#120](https://github.com/sansyrox/robyn/issues/120)
- Inconsistency in steps mentioned in Readme to run locally  [\#119](https://github.com/sansyrox/robyn/issues/119)
- Async web socket support [\#116](https://github.com/sansyrox/robyn/issues/116)
- Reveal Logo to be removed from Future Roadmap [\#107](https://github.com/sansyrox/robyn/issues/107)
- Dead Link for Test Drive Button on Robyn Landing Page  [\#106](https://github.com/sansyrox/robyn/issues/106)
- Add issue template, pr template and community guidelines [\#105](https://github.com/sansyrox/robyn/issues/105)
- For v0.7.0 [\#72](https://github.com/sansyrox/robyn/issues/72)
- Add better support for requests and response! [\#13](https://github.com/sansyrox/robyn/issues/13)

**Merged pull requests:**

- Add async support in WS [\#134](https://github.com/sansyrox/robyn/pull/134) ([sansyrox](https://github.com/sansyrox))
- Add help messages and simplify 'dev' option [\#128](https://github.com/sansyrox/robyn/pull/128) ([Kludex](https://github.com/Kludex))
- Apply Python highlight on api.md [\#126](https://github.com/sansyrox/robyn/pull/126) ([Kludex](https://github.com/Kludex))
- Update comparison.md [\#124](https://github.com/sansyrox/robyn/pull/124) ([Kludex](https://github.com/Kludex))
- Update comparison.md [\#123](https://github.com/sansyrox/robyn/pull/123) ([Kludex](https://github.com/Kludex))
- Fix readme documentation [\#122](https://github.com/sansyrox/robyn/pull/122) ([sansyrox](https://github.com/sansyrox))
- Release v0.9.0 Changelog [\#121](https://github.com/sansyrox/robyn/pull/121) ([sansyrox](https://github.com/sansyrox))
- \[FEAT\] Open Source Contribution Templates [\#118](https://github.com/sansyrox/robyn/pull/118) ([shivaylamba](https://github.com/shivaylamba))
- FIX : Wrong link for Test Drive [\#117](https://github.com/sansyrox/robyn/pull/117) ([shivaylamba](https://github.com/shivaylamba))

## [v0.9.0](https://github.com/sansyrox/robyn/tree/v0.9.0) (2021-12-01)

[Full Changelog](https://github.com/sansyrox/robyn/compare/v0.8.1...v0.9.0)

**Closed issues:**

- Add more HTTP methods [\#74](https://github.com/sansyrox/robyn/issues/74)

**Merged pull requests:**

- Fix default url bug [\#111](https://github.com/sansyrox/robyn/pull/111) ([sansyrox](https://github.com/sansyrox))
- Web socket integration attempt 2 [\#109](https://github.com/sansyrox/robyn/pull/109) ([sansyrox](https://github.com/sansyrox))

## [v0.8.1](https://github.com/sansyrox/robyn/tree/v0.8.1) (2021-11-17)

[Full Changelog](https://github.com/sansyrox/robyn/compare/v0.8.0...v0.8.1)

**Fixed bugs:**

- The default start is running the server at '0.0.0.0' instead of '127.0.0.1' [\#110](https://github.com/sansyrox/robyn/issues/110)

## [v0.8.0](https://github.com/sansyrox/robyn/tree/v0.8.0) (2021-11-10)

[Full Changelog](https://github.com/sansyrox/robyn/compare/v0.7.1...v0.8.0)

**Closed issues:**

- Share the TCP web socket across different cores [\#91](https://github.com/sansyrox/robyn/issues/91)
- Improve the router [\#52](https://github.com/sansyrox/robyn/issues/52)
- \[Stretch Goal\] Create a a way of writing async request [\#32](https://github.com/sansyrox/robyn/issues/32)
- Improve the router [\#29](https://github.com/sansyrox/robyn/issues/29)

**Merged pull requests:**

- Fix the failing testing suite! [\#100](https://github.com/sansyrox/robyn/pull/100) ([sansyrox](https://github.com/sansyrox))
- Requests object is now optional [\#99](https://github.com/sansyrox/robyn/pull/99) ([sansyrox](https://github.com/sansyrox))
- Add socket sharing [\#94](https://github.com/sansyrox/robyn/pull/94) ([sansyrox](https://github.com/sansyrox))

## [v0.7.1](https://github.com/sansyrox/robyn/tree/v0.7.1) (2021-10-28)

[Full Changelog](https://github.com/sansyrox/robyn/compare/v0.7.0...v0.7.1)

**Closed issues:**

- Remove the solution using dockerisation of tests [\#98](https://github.com/sansyrox/robyn/issues/98)
- Functions not working without request param [\#96](https://github.com/sansyrox/robyn/issues/96)
- Add actix router [\#85](https://github.com/sansyrox/robyn/issues/85)
- Request apart from GET are not working in directory subroutes [\#79](https://github.com/sansyrox/robyn/issues/79)
- Add the ability to share the server across the network [\#69](https://github.com/sansyrox/robyn/issues/69)
- Add the ability to view headers in the HTTP Methods [\#54](https://github.com/sansyrox/robyn/issues/54)
- Add tests! [\#8](https://github.com/sansyrox/robyn/issues/8)

## [v0.7.0](https://github.com/sansyrox/robyn/tree/v0.7.0) (2021-10-03)

[Full Changelog](https://github.com/sansyrox/robyn/compare/v0.6.1...v0.7.0)

**Closed issues:**

- Robyn the replacement of Quart [\#86](https://github.com/sansyrox/robyn/issues/86)
- Add Pytest support for the test endpoints [\#81](https://github.com/sansyrox/robyn/issues/81)

**Merged pull requests:**

- Finally completed router integration [\#90](https://github.com/sansyrox/robyn/pull/90) ([sansyrox](https://github.com/sansyrox))
- Address clippy lints [\#89](https://github.com/sansyrox/robyn/pull/89) ([SanchithHegde](https://github.com/SanchithHegde))
- Initial docs update [\#83](https://github.com/sansyrox/robyn/pull/83) ([sansyrox](https://github.com/sansyrox))
- Add the basics of python testing [\#82](https://github.com/sansyrox/robyn/pull/82) ([sansyrox](https://github.com/sansyrox))
- Add a new landing page [\#80](https://github.com/sansyrox/robyn/pull/80) ([sansyrox](https://github.com/sansyrox))

## [v0.6.1](https://github.com/sansyrox/robyn/tree/v0.6.1) (2021-08-30)

[Full Changelog](https://github.com/sansyrox/robyn/compare/v0.6.0...v0.6.1)

**Closed issues:**

- Make a new release [\#71](https://github.com/sansyrox/robyn/issues/71)
- Update to the pyo3 v0.14 [\#63](https://github.com/sansyrox/robyn/issues/63)
- Add the support to serve static directories [\#55](https://github.com/sansyrox/robyn/issues/55)
- Add support for mounting directory [\#38](https://github.com/sansyrox/robyn/issues/38)

**Merged pull requests:**

- Add the base of http requests [\#78](https://github.com/sansyrox/robyn/pull/78) ([sansyrox](https://github.com/sansyrox))
- Add default port and a variable url [\#77](https://github.com/sansyrox/robyn/pull/77) ([sansyrox](https://github.com/sansyrox))
- Make the request object accessible in every route [\#76](https://github.com/sansyrox/robyn/pull/76) ([sansyrox](https://github.com/sansyrox))
- Add the basics for circle ci and testing framework [\#67](https://github.com/sansyrox/robyn/pull/67) ([sansyrox](https://github.com/sansyrox))
- Update to pyo3 v0.14 [\#65](https://github.com/sansyrox/robyn/pull/65) ([sansyrox](https://github.com/sansyrox))
- Add the static directory serving [\#64](https://github.com/sansyrox/robyn/pull/64) ([sansyrox](https://github.com/sansyrox))
- Create a request object [\#61](https://github.com/sansyrox/robyn/pull/61) ([sansyrox](https://github.com/sansyrox))
- Add the ability to add body in PUT, PATCH and DELETE [\#60](https://github.com/sansyrox/robyn/pull/60) ([sansyrox](https://github.com/sansyrox))
- Implement a working dev server [\#40](https://github.com/sansyrox/robyn/pull/40) ([sansyrox](https://github.com/sansyrox))
- Use Actix as base [\#35](https://github.com/sansyrox/robyn/pull/35) ([JackThomson2](https://github.com/JackThomson2))

## [v0.6.0](https://github.com/sansyrox/robyn/tree/v0.6.0) (2021-08-11)

[Full Changelog](https://github.com/sansyrox/robyn/compare/v0.5.3...v0.6.0)

**Closed issues:**

- Add body support for PUT, POST and PATCH [\#53](https://github.com/sansyrox/robyn/issues/53)
- Away with limited internet access till 1st August [\#51](https://github.com/sansyrox/robyn/issues/51)
- Add doc stings [\#42](https://github.com/sansyrox/robyn/issues/42)
- OSX builds are failing [\#41](https://github.com/sansyrox/robyn/issues/41)
- Add a dev server implementation [\#37](https://github.com/sansyrox/robyn/issues/37)
- Mini Roadmap | A list of issues that would require fixing [\#19](https://github.com/sansyrox/robyn/issues/19)
- Add support for Object/JSON Return Type! [\#9](https://github.com/sansyrox/robyn/issues/9)

## [v0.5.3](https://github.com/sansyrox/robyn/tree/v0.5.3) (2021-07-12)

[Full Changelog](https://github.com/sansyrox/robyn/compare/v0.5.2...v0.5.3)

**Merged pull requests:**

- Improve the HTML file serving [\#46](https://github.com/sansyrox/robyn/pull/46) ([sansyrox](https://github.com/sansyrox))
- Add the basics to add serving of static files [\#36](https://github.com/sansyrox/robyn/pull/36) ([sansyrox](https://github.com/sansyrox))

## [v0.5.2](https://github.com/sansyrox/robyn/tree/v0.5.2) (2021-07-11)

[Full Changelog](https://github.com/sansyrox/robyn/compare/v0.5.1...v0.5.2)

## [v0.5.1](https://github.com/sansyrox/robyn/tree/v0.5.1) (2021-07-10)

[Full Changelog](https://github.com/sansyrox/robyn/compare/v0.5.0...v0.5.1)

**Closed issues:**

- Make html file serving more robust [\#45](https://github.com/sansyrox/robyn/issues/45)
- Try to serve individual static files using vanilla rust [\#43](https://github.com/sansyrox/robyn/issues/43)
- Error on import  [\#16](https://github.com/sansyrox/robyn/issues/16)
- Add multiple process sharing [\#2](https://github.com/sansyrox/robyn/issues/2)

## [v0.5.0](https://github.com/sansyrox/robyn/tree/v0.5.0) (2021-07-01)

[Full Changelog](https://github.com/sansyrox/robyn/compare/v0.4.1...v0.5.0)

**Closed issues:**

- QPS drops drastically after processing many requests [\#31](https://github.com/sansyrox/robyn/issues/31)
- Improve the way you parse TCP streams [\#30](https://github.com/sansyrox/robyn/issues/30)
- Re-introduce thread pool for the sync functions \(maybe\) [\#22](https://github.com/sansyrox/robyn/issues/22)
- Add async listener object in rust stream! [\#11](https://github.com/sansyrox/robyn/issues/11)

**Merged pull requests:**

- Make the server http compliant [\#33](https://github.com/sansyrox/robyn/pull/33) ([sansyrox](https://github.com/sansyrox))

## [v0.4.1](https://github.com/sansyrox/robyn/tree/v0.4.1) (2021-06-26)

[Full Changelog](https://github.com/sansyrox/robyn/compare/0.4.0...v0.4.1)

**Closed issues:**

- Add PyPi Metadata [\#5](https://github.com/sansyrox/robyn/issues/5)

**Merged pull requests:**

- Build and publish wheels on GitHub Actions [\#26](https://github.com/sansyrox/robyn/pull/26) ([messense](https://github.com/messense))
- Code cleanup using PyFunction type [\#25](https://github.com/sansyrox/robyn/pull/25) ([sansyrox](https://github.com/sansyrox))
- Add non blocking sync functions [\#23](https://github.com/sansyrox/robyn/pull/23) ([sansyrox](https://github.com/sansyrox))
- Add support for sync functions [\#20](https://github.com/sansyrox/robyn/pull/20) ([sansyrox](https://github.com/sansyrox))

## [0.4.0](https://github.com/sansyrox/robyn/tree/0.4.0) (2021-06-22)

[Full Changelog](https://github.com/sansyrox/robyn/compare/v0.3.0...0.4.0)

**Closed issues:**

- Add support for Sync functions as well! [\#7](https://github.com/sansyrox/robyn/issues/7)

## [v0.3.0](https://github.com/sansyrox/robyn/tree/v0.3.0) (2021-06-21)

[Full Changelog](https://github.com/sansyrox/robyn/compare/v0.2.3...v0.3.0)

**Closed issues:**

- Architecture link in readme redirects to raw content [\#18](https://github.com/sansyrox/robyn/issues/18)
- Link pointing to the wrong destination [\#6](https://github.com/sansyrox/robyn/issues/6)

**Merged pull requests:**

- Pure tokio [\#17](https://github.com/sansyrox/robyn/pull/17) ([JackThomson2](https://github.com/JackThomson2))
- Remove Mutex lock on Threadpool and routes [\#15](https://github.com/sansyrox/robyn/pull/15) ([JackThomson2](https://github.com/JackThomson2))

## [v0.2.3](https://github.com/sansyrox/robyn/tree/v0.2.3) (2021-06-18)

[Full Changelog](https://github.com/sansyrox/robyn/compare/c14f52e6faa79917e89de4220590da7bf28f6a65...v0.2.3)

**Closed issues:**

- Improve async runtime [\#3](https://github.com/sansyrox/robyn/issues/3)



\* *This Changelog was automatically generated by [github_changelog_generator](https://github.com/github-changelog-generator/github-changelog-generator)*
