# Luna Xhigh: Twenty Distinct Seeds

Completed artifact summary; raw outputs remain untouched.

Returned 19/20; checked 19; fully runnable 5; full mechanical acceptance 1; judged 5.

| Pack | Seed words | Generation | Runtime /100 | Tests | Reference words | Quality /9 | Diversity /9 | Output tokens |
| --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: |
| 01 bakery | basket, icing, uneven | error | - | - | - | - | - | - |
| 02 puppets | curtain, button, whisper | completed | 0 | fail | 863 | - | - | 46794 |
| 03 greenhouse | seedling, shade, thirsty | completed | 100 | pass | 809 | 8 | 2 | 39299 |
| 04 seaside | map, tide, mistake | completed | 0 | fail | 925 | - | - | 51642 |
| 05 library | bookmark, ladder, promise | completed | 100 | pass | 992 | 8 | 3 | 69349 |
| 06 snow | sled, mittens, patient | completed | not tested | - | None | - | - | 60204 |
| 07 picnic | blanket, crumbs, gust | completed | 0 | fail | 926 | - | - | 46427 |
| 08 music | drum, ribbon, hesitate | completed | 100 | fail | 1208 | 7 | 2 | 38857 |
| 09 market | scale, apples, honest | completed | 100 | fail | 873 | 8 | 3 | 53583 |
| 10 camp | lantern, shadow, brave | completed | 0 | fail | 1139 | - | - | 59219 |
| 11 pottery | clay, sponge, crooked | completed | 0 | fail | 890 | - | - | 41846 |
| 12 orchard | pear, crate, reach | completed | 0 | fail | 760 | - | - | 41846 |
| 13 costume | cape, mirror, borrow | completed | 0 | fail | 968 | - | - | 42243 |
| 14 pond | boat, net, stuck | completed | 0 | fail | 1114 | - | - | 44112 |
| 15 repair | wheel, spanner, rattle | completed | 100 | fail | 793 | 8 | 2 | 53913 |
| 16 museum | torch, label, puzzled | completed | 0 | fail | 845 | - | - | 51646 |
| 17 laundry | peg, sheet, shelter | completed | 0 | fail | 1103 | - | - | 52494 |
| 18 trail | compass, puddle, shortcut | completed | 98 | fail | 977 | - | - | 41555 |
| 19 festival | bunting, string, welcome | completed | 3 | fail | 1049 | - | - | 38598 |
| 20 biscuit | cutter, flour, share | completed | 0 | fail | 1139 | - | - | 46818 |

Quality is conditional on 100/100 runnable packs; no repairs. One prompt per distinct scenario; no matched 64k control batch.

See `luna_xhigh_128k_20_summary.json` for failures, outcomes, usage and costs.
See `LUNA_XHIGH_128K_20_SAMPLES.md` for a separate manual-reading sample, not the paid judge selection.
Snow's inventory JSON fails checker preflight; its runtime is untested, not 100 observed runtime failures.
