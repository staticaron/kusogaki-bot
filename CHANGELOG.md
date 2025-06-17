# Changelog

## [0.8.0](https://github.com/kusogaki-events/kusogaki-bot/compare/v0.7.1...v0.8.0) (2025-06-17)


### Features

* add recommendation command ([d583e99](https://github.com/kusogaki-events/kusogaki-bot/commit/d583e99b466b98c590698586e81db378fa8ed5b9))
* animanga recommendation groundwork ([2bea7f0](https://github.com/kusogaki-events/kusogaki-bot/commit/2bea7f0104c5569259ee4b31de7e1570011cca16))
* Show recommendation mean score in embed ([bf056a7](https://github.com/kusogaki-events/kusogaki-bot/commit/bf056a7f2df4309814acc8444adb8403a886e8be))
* update rec UI to use embeds, add ability to show all recs ([c95a02a](https://github.com/kusogaki-events/kusogaki-bot/commit/c95a02aeecafe54fc048ce0b4cbc9c7c9a230ace))
* use prev/next buttons to cycle through recommendations ([aecf30e](https://github.com/kusogaki-events/kusogaki-bot/commit/aecf30eb169b3b2a539f1b7d2552f83a1c8a6f1e))
* weight favorited anime in recs ([1ac5187](https://github.com/kusogaki-events/kusogaki-bot/commit/1ac51872d1ff139c2c2f3bf00a22ac24b505b6b7))


### Bug Fixes

* add httpx dependency ([6600750](https://github.com/kusogaki-events/kusogaki-bot/commit/6600750e0050b8620c038bb96785132276b2c6e9))
* add random rec score before sorting to avoid mismatched entries ([333878d](https://github.com/kusogaki-events/kusogaki-bot/commit/333878d77cfeecb024efe365b485e80d941b776c))
* add rate limiting to medialist API requests ([90b822a](https://github.com/kusogaki-events/kusogaki-bot/commit/90b822a8733e3c3b3fd7d6b80f392271e466758f))
* adjust retry wait period ([b8a3af6](https://github.com/kusogaki-events/kusogaki-bot/commit/b8a3af629dc41a9e94741f6c6f06fb14bb8a7f10))
* clean up deprecated vars + code ([7656cca](https://github.com/kusogaki-events/kusogaki-bot/commit/7656ccadcaba40ba8bcb7ebde971f742e162eff1))
* divide by zero when no scores exist; scoring algorithm changes ([3f913fc](https://github.com/kusogaki-events/kusogaki-bot/commit/3f913fc3332b6c4f11eb769ea36398347aeb7de0))
* do not recommend dropped shows ([2ffdb50](https://github.com/kusogaki-events/kusogaki-bot/commit/2ffdb50529920b75317cdcb45f4bb50c2a33fc56))
* error handling when request does not return valid data ([4bab58b](https://github.com/kusogaki-events/kusogaki-bot/commit/4bab58b7d7614eeb856e9f8cace5e5af993109e0))
* exit nicely on command error ([bffa2c0](https://github.com/kusogaki-events/kusogaki-bot/commit/bffa2c04f9551968685e72ba8b308978de2eb0f7))
* improve logging ([5e4cb5a](https://github.com/kusogaki-events/kusogaki-bot/commit/5e4cb5a6c723d64ef84b478aa41bdd2dc91af2d4))
* raise chunk size for less requests ([c65d76d](https://github.com/kusogaki-events/kusogaki-bot/commit/c65d76d958d7309b215500abea4bfae1dc962829))
* raise request error properly if request fails ([225ab85](https://github.com/kusogaki-events/kusogaki-bot/commit/225ab857faec012b577f112980f4051e72a4e963))
* rec embed formatting ([85a56ab](https://github.com/kusogaki-events/kusogaki-bot/commit/85a56ab1eea8d0b9945ea7655cca4ef2c95b68ea))
* remove dropped shows from rec consideration ([a718639](https://github.com/kusogaki-events/kusogaki-bot/commit/a7186392131d8dee6c996969cf0c5bc9d542b9b7))
* remove erroneus genre filtering ([c36e7d9](https://github.com/kusogaki-events/kusogaki-bot/commit/c36e7d9213d50b15b01a391d914a43374a2bdd0d))
* specifying media type without genre now returns correctly ([327c3cb](https://github.com/kusogaki-events/kusogaki-bot/commit/327c3cb8af78ad89c323196d743d87e873fec061))
* use shared embed type instead of discord's ([54822b3](https://github.com/kusogaki-events/kusogaki-bot/commit/54822b3e938440ea7ff30f14a3625b2e44cfb62f))
* use weight defined in model ([139b62a](https://github.com/kusogaki-events/kusogaki-bot/commit/139b62aefb7f55e772a73644af808d2b14a30a71))
* zero division error handling ([af6f6e9](https://github.com/kusogaki-events/kusogaki-bot/commit/af6f6e99deca7deb5df3453738d242db7514b64a))


### Documentation

* add help information for rec commands ([f156ff2](https://github.com/kusogaki-events/kusogaki-bot/commit/f156ff20772e2df606942f55cf1949416cbec6c0))
* add rec command ([1bdd779](https://github.com/kusogaki-events/kusogaki-bot/commit/1bdd7796cc1dc7efa5838548f90b1d7d6cb36870))

## [0.7.1](https://github.com/kusogaki-events/kusogaki-bot/compare/v0.7.0...v0.7.1) (2025-05-20)


### Miscellaneous Chores

* release 0.7.1 ([27978de](https://github.com/kusogaki-events/kusogaki-bot/commit/27978deb74d5b1eb721643499c1d842c913d170e))

## [0.7.0](https://github.com/kusogaki-events/kusogaki-bot/compare/v0.6.0...v0.7.0) (2025-03-10)


### Features

* join GTA quiz with button instead of message ([4956629](https://github.com/kusogaki-events/kusogaki-bot/commit/4956629c3bcde31f41c5e20e48372854addd833c))
* join GTA quiz with button instead of message ([1bd5144](https://github.com/kusogaki-events/kusogaki-bot/commit/1bd51445a65707aaca2a9a291b4c59df7b6df80e))
* show joined players in game start embed ([9933d2d](https://github.com/kusogaki-events/kusogaki-bot/commit/9933d2def923831ea83b0d68fb0e8a24c85b54b3))


### Bug Fixes

* make successful player join message visible ([9ef7b90](https://github.com/kusogaki-events/kusogaki-bot/commit/9ef7b9072778eb85b327c198fc10ccd9e8f30a29))


### Documentation

* add example to replace join example ([784dcaa](https://github.com/kusogaki-events/kusogaki-bot/commit/784dcaa12610719c94a6b59a6f038154fe171b0f))
* fix pydoc wording ([fc04d26](https://github.com/kusogaki-events/kusogaki-bot/commit/fc04d26f28fb949f78e794b9d30fdf8655b12989))
* remove deprecated gq join command ([9c31c72](https://github.com/kusogaki-events/kusogaki-bot/commit/9c31c72139071fb7f34942bfc8849d9eca1a0eb5))
* remove join command from list ([b6bf880](https://github.com/kusogaki-events/kusogaki-bot/commit/b6bf880fb9b64684711899feb9d6c4b02f0b3b11))
* remove references to gq join command ([357fe01](https://github.com/kusogaki-events/kusogaki-bot/commit/357fe01313826847ea5b370a3caf8462f5a6c8d8))

## [0.6.0](https://github.com/kusogaki-events/kusogaki-bot/compare/v0.5.6...v0.6.0) (2025-03-01)


### Features

* added Miku ([3723ba6](https://github.com/kusogaki-events/kusogaki-bot/commit/3723ba623e978c1d6703348a71f66da773d6453a))

## [0.5.6](https://github.com/kusogaki-events/kusogaki-bot/compare/v0.5.5...v0.5.6) (2025-02-19)


### Bug Fixes

* prevent duplicate incorrect options ([ee4e2ce](https://github.com/kusogaki-events/kusogaki-bot/commit/ee4e2ce2307bdd1c1424616e47ada40ec866526d))

## [0.5.5](https://github.com/kusogaki-events/kusogaki-bot/compare/v0.5.4...v0.5.5) (2025-02-17)


### Bug Fixes

* filter out duplicate titles in GTA options ([bd3bb0c](https://github.com/kusogaki-events/kusogaki-bot/commit/bd3bb0cd291fc648771ddeabd1b4f8fcfd3e7303))

## [0.5.4](https://github.com/kusogaki-events/kusogaki-bot/compare/v0.5.3...v0.5.4) (2025-02-10)


### Documentation

* update docs for uv usage ([a6aee5d](https://github.com/kusogaki-events/kusogaki-bot/commit/a6aee5d4e1080d806f9d0da9ed064965fe16ca35))

## [0.5.3](https://github.com/kusogaki-events/kusogaki-bot/compare/v0.5.2...v0.5.3) (2025-02-10)


### Bug Fixes

* wait until a user is eliminated to show high score ([43305c0](https://github.com/kusogaki-events/kusogaki-bot/commit/43305c0ac27a0bb2db81c0c8ffa8540fe6e73bdd))

## [0.5.2](https://github.com/kusogaki-events/kusogaki-bot/compare/v0.5.1...v0.5.2) (2025-02-08)


### Bug Fixes

* add correct answer feedback if no player answers ([6848e42](https://github.com/kusogaki-events/kusogaki-bot/commit/6848e426d9695b70d78da25bc24b3cf447100726))

## [0.5.1](https://github.com/kusogaki-events/kusogaki-bot/compare/v0.5.0...v0.5.1) (2025-02-08)


### Bug Fixes

* acknowledge button press guess the anime ([63a2168](https://github.com/kusogaki-events/kusogaki-bot/commit/63a21680fa02771bb3c1c2ec916c51966633143b))
* delay gta answer feedback until end of round ([a3dce20](https://github.com/kusogaki-events/kusogaki-bot/commit/a3dce20a10831b9d5cb0169054aea48229eda2c1))


### Documentation

* remove reference to round feedback in AnswerView ([373caa8](https://github.com/kusogaki-events/kusogaki-bot/commit/373caa8c6a0012c4a84bb1263709f4d3987e6cb8))

## [0.5.0](https://github.com/kusogaki-events/kusogaki-bot/compare/v0.4.0...v0.5.0) (2025-01-24)


### Features

* add central core exception classes ([c09db68](https://github.com/kusogaki-events/kusogaki-bot/commit/c09db681ca0f7b43faefdc61039648ba034c424d))
* add central core exception classes ([28fd2fc](https://github.com/kusogaki-events/kusogaki-bot/commit/28fd2fc1f309d3fdf861c3ba2330f9713e3d5eca))
* add core database connection file ([db9a590](https://github.com/kusogaki-events/kusogaki-bot/commit/db9a5904c9a00b6ff135cb7893552de925d08905))
* add core database connection file ([5a22431](https://github.com/kusogaki-events/kusogaki-bot/commit/5a22431419bbfc422ed7bef4341ec92f8f23a394))
* add new base cog for all cogs ([7a26eaa](https://github.com/kusogaki-events/kusogaki-bot/commit/7a26eaa334303aadeb5f6ca9d182a778f5c7677c))
* add new base cog for all cogs ([2958db4](https://github.com/kusogaki-events/kusogaki-bot/commit/2958db49dc3d084e689519bec77f73ae18ab0568))
* add new gta game logic ([9989f6d](https://github.com/kusogaki-events/kusogaki-bot/commit/9989f6d82ff63909f91118bd1d55fb94eb8ff76f))
* add new gta game logic ([434c542](https://github.com/kusogaki-events/kusogaki-bot/commit/434c542b299e7b7adfa04382d0786c96bccee953))
* add updated awaiz food tracker ([3e5ce0c](https://github.com/kusogaki-events/kusogaki-bot/commit/3e5ce0c269935e59fad9fe7a87bd9da149e86536))
* add updated awaiz food tracker ([7f21476](https://github.com/kusogaki-events/kusogaki-bot/commit/7f21476c81c2af1f866adbbcb1f9eebb832191d2))
* make food tracker automatic ([95b2827](https://github.com/kusogaki-events/kusogaki-bot/commit/95b282721d529ef92c80325771a5adc0c4b0b446))
* make food tracker automatic ([4d75ccd](https://github.com/kusogaki-events/kusogaki-bot/commit/4d75ccd0634b3ae2b28c14634da12629558be152))
* migration of poll-command logic to new structure ([130a511](https://github.com/kusogaki-events/kusogaki-bot/commit/130a511d4f8bf62a4736bd2bd044dc4a12a9e2f9))
* reload command ([f5aff4d](https://github.com/kusogaki-events/kusogaki-bot/commit/f5aff4dbf917ac59a8ecfa2d91d41fe117fc6ec4))


### Bug Fixes

* fix typo in ci failure workflow ([28fffba](https://github.com/kusogaki-events/kusogaki-bot/commit/28fffba77b5e54c49cd88f0e4e3e09c396ed7ee8))
* incomplete docstring ([18f2c10](https://github.com/kusogaki-events/kusogaki-bot/commit/18f2c10dcff2c9bf7bc51afc35ee916e16246fba))
* linting errors ([08b2e9a](https://github.com/kusogaki-events/kusogaki-bot/commit/08b2e9a7ae206ebed61f4bcc81ce33d845e3db28))
* linting issues ([41caecb](https://github.com/kusogaki-events/kusogaki-bot/commit/41caecb717cff84fda5cfe5dbe33aca470370940))
* remove import from ci failure workflow ([7605b52](https://github.com/kusogaki-events/kusogaki-bot/commit/7605b528e62f1327a9a86840b4cfbd4578e42241))


### Documentation

* add ADR for project restructuring to feature-based architecture ([93e2356](https://github.com/kusogaki-events/kusogaki-bot/commit/93e23562a3e2c1e2462cfdee740ff367fc0564e9))
* add ADR for project restructuring to feature-based architecture ([4340a8e](https://github.com/kusogaki-events/kusogaki-bot/commit/4340a8ec43b68be904d6304c7e8dbd4698eada0a))
* add development mode to contributing guidelines ([46c1251](https://github.com/kusogaki-events/kusogaki-bot/commit/46c12510f34ed3da4f8e4308072667fc7e7c50d0))
* add mention of auto food tracking for awaiz in readme ([f10af81](https://github.com/kusogaki-events/kusogaki-bot/commit/f10af812b900dc2f316f346b90b6fa4af2fd8c00))
* fix typo on readme ([2472aec](https://github.com/kusogaki-events/kusogaki-bot/commit/2472aecadb1dd82dfac2157a528be0567d8f8f97))
* update readme to have current commands ([d17fb26](https://github.com/kusogaki-events/kusogaki-bot/commit/d17fb260aafe81e645da0e620d94863a05dc5dc5))

## [0.4.0](https://github.com/kusogaki-events/kusogaki-bot/compare/v0.3.1...v0.4.0) (2024-12-31)


### Features

* add help command to bot ([dcf1dfa](https://github.com/kusogaki-events/kusogaki-bot/commit/dcf1dfaae95bcfa4205d9cfd486f1c8c3b12fabd))

## [0.3.1](https://github.com/kusogaki-events/kusogaki-bot/compare/v0.3.0...v0.3.1) (2024-12-01)


### Bug Fixes

* use correct database model ([b4cbba4](https://github.com/kusogaki-events/kusogaki-bot/commit/b4cbba4252076a7783a415cd03d81783eacc1cb9))


### Documentation

* add status badge to readme ([88fb11a](https://github.com/kusogaki-events/kusogaki-bot/commit/88fb11a2851dc70b851dd5e04313dc8d2193fb43))

## [0.3.0](https://github.com/kusogaki-events/kusogaki-bot/compare/v0.2.0...v0.3.0) (2024-12-01)


### Features

* convert redis to postgresql database ([48516ee](https://github.com/kusogaki-events/kusogaki-bot/commit/48516ee73e50f31ad66a262405fee020a08c3b94))

## [0.2.0](https://github.com/kusogaki-events/kusogaki-bot/compare/v0.1.0...v0.2.0) (2024-11-30)


### Features

* add cheat ping command ([f5810c6](https://github.com/kusogaki-events/kusogaki-bot/commit/f5810c6abe59c16da3f42226f891a5edac587dfd))

## 0.1.0 (2024-11-28)


### Features

* add awaiz food counter command ([4c19cb7](https://github.com/kusogaki-events/kusogaki-bot/commit/4c19cb78a87b9b627920776f09d6110cbc54b03e))
* add base cog for common error handling ([2fd6138](https://github.com/kusogaki-events/kusogaki-bot/commit/2fd6138ce6e8d931ecfe688d40f962ce0e36bf54))
* add database solution for reminders ([cb45dd2](https://github.com/kusogaki-events/kusogaki-bot/commit/cb45dd24369173b0b059c83919ce01dd86364afe))
* add gta quiz game ([484ac0b](https://github.com/kusogaki-events/kusogaki-bot/commit/484ac0b3747d516fd6b9300614ccbf07610aaaa5))
* add permissions model for cogs ([6f34dbb](https://github.com/kusogaki-events/kusogaki-bot/commit/6f34dbb1a971ae74e6a96dbba51b84260890fbbf))
* add poll creation command ([60d2180](https://github.com/kusogaki-events/kusogaki-bot/commit/60d21800b309877b5597b7df90c36e18b2d19f47))
* add reminders command ([f9524de](https://github.com/kusogaki-events/kusogaki-bot/commit/f9524de2aeafd00cfbfe2d93b8bff3cb7d6a3e59))
* add scheduled tasks ([c02207e](https://github.com/kusogaki-events/kusogaki-bot/commit/c02207ed44e4de6e89a579306e235f2fdb3c4e71))
* add shared embed utility class ([bad72e7](https://github.com/kusogaki-events/kusogaki-bot/commit/bad72e75b897c8ec5ec6149ef4a273be0588e9c9))
* add timeout feature if no one answers in time ([3217b50](https://github.com/kusogaki-events/kusogaki-bot/commit/3217b50679ee78e3d827669ef585633392d50e58))
* Added Cogs with ping command ([fba212c](https://github.com/kusogaki-events/kusogaki-bot/commit/fba212c20976aebe8f878ad5a1aa018d1584ef1c))
* allow polls on book club channel ([e133c37](https://github.com/kusogaki-events/kusogaki-bot/commit/e133c37d04da17e4f45ac950d795ef0370e19a0f))


### Bug Fixes

* add environment variables to dockerfile ([d785210](https://github.com/kusogaki-events/kusogaki-bot/commit/d785210e0632b1ae60682628aa50dc85b936b646))
* add service specifier for railway deploy ([d48228d](https://github.com/kusogaki-events/kusogaki-bot/commit/d48228d21b3a06dab4ec64dd885a59e7c5e79eb5))
* correct path separators in .dockerignore ([0c111ab](https://github.com/kusogaki-events/kusogaki-bot/commit/0c111ab4c0ab97cd1ec007edac13e4e737baaa31))
* fix formatting script if no base args are provided ([33e0d28](https://github.com/kusogaki-events/kusogaki-bot/commit/33e0d28664384b04ec47101eeb114358eb440597))
* fix issues with ci and release workflow definitions ([d30a3c3](https://github.com/kusogaki-events/kusogaki-bot/commit/d30a3c3e74c6dfb6996122ece51daeb58897d9f0))
* fix typo on release workflow ([923751a](https://github.com/kusogaki-events/kusogaki-bot/commit/923751a8581d1ed7b6d93a7c03520052efcad763))
* fixed the f-string error ([25c2c9e](https://github.com/kusogaki-events/kusogaki-bot/commit/25c2c9e1293afb05593fa8c1bde587999010736e))
* only load .env in local dev ([83ef2ed](https://github.com/kusogaki-events/kusogaki-bot/commit/83ef2edf598137fc7836aab0eaee581cb48faaa7))
* remove deploy on push ([c1d0e38](https://github.com/kusogaki-events/kusogaki-bot/commit/c1d0e38cd2ed055369b679526d74924e3404653d))
* remove invalid key in railway config ([eeaddba](https://github.com/kusogaki-events/kusogaki-bot/commit/eeaddba3be3d3e942931ce6271f6abd56550f8d3))
* remove un-needed health check path ([2afca30](https://github.com/kusogaki-events/kusogaki-bot/commit/2afca308bb8e97553d8f90adf9e627d08ea3add8))


### Performance Improvements

* made the kuso command more versatile ([972fb6f](https://github.com/kusogaki-events/kusogaki-bot/commit/972fb6fffee8280773fbda0e8377f4c77af1c430))


### Documentation

* add awaiz food counter commands to readme ([0d569c7](https://github.com/kusogaki-events/kusogaki-bot/commit/0d569c7d38b298f74b862ce3fcc81c3021cd1002))
* add basic readme content ([a318d59](https://github.com/kusogaki-events/kusogaki-bot/commit/a318d59125d34c964d5ae66dd94469ece1f0cc72))
* add bug issue template ([5828af6](https://github.com/kusogaki-events/kusogaki-bot/commit/5828af68dd86bbff0ec2b9334aa0208753356254))
* add changelog file for releases ([00de2cd](https://github.com/kusogaki-events/kusogaki-bot/commit/00de2cd9a9dfce2bcdf8087054e0d7f52b5b9c8e))
* add current commands to readme ([2d33f56](https://github.com/kusogaki-events/kusogaki-bot/commit/2d33f567580ee0ce636341ce4b34d65cd81d1ed7))
* add development contributing docs ([8843f5f](https://github.com/kusogaki-events/kusogaki-bot/commit/8843f5fd8a92cc245b3245442fc8af3a93c86127))
* add development contributing file (un-written) ([a15f2fd](https://github.com/kusogaki-events/kusogaki-bot/commit/a15f2fdc3c733407c2c4697f5370e6824abf5a76))
* add feature request template ([0b0b340](https://github.com/kusogaki-events/kusogaki-bot/commit/0b0b340df28d3d5468032926c97d3ef3f1a63afd))
* add first draft for contributing docs ([5c3cb8b](https://github.com/kusogaki-events/kusogaki-bot/commit/5c3cb8b78bf96aa19208144d1279f8429d83ee63))
* add pull request template ([6a03136](https://github.com/kusogaki-events/kusogaki-bot/commit/6a031364f2fc0298d5787313d02ea5cb8609a1bb))
* finish contributing guidelines file ([69ef5ec](https://github.com/kusogaki-events/kusogaki-bot/commit/69ef5ec1a91c12c90e76f6ec5a72b7e27c9c79fc))
* readd github banner ([a8d8a00](https://github.com/kusogaki-events/kusogaki-bot/commit/a8d8a00c825cfb2f75e970b006f18c3757bfcdd6))
* rename github banner image ([9f5adf6](https://github.com/kusogaki-events/kusogaki-bot/commit/9f5adf6ff3387273ad775ea8e640a99e27a69e90))
* update readme banner image ([4c1870f](https://github.com/kusogaki-events/kusogaki-bot/commit/4c1870f332b34bc1bf6f5cdb41d2b1a621d44519))
* update readme for contributions ([ba1e51f](https://github.com/kusogaki-events/kusogaki-bot/commit/ba1e51febc8ef2e32838f9ec9136a6757cd7772c))
