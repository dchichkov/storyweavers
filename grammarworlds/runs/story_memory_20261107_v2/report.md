# Intact stories as reusable annotated memory

140 source stories from seven existing worlds. Original text and sampled token order are preserved and each source history replays.
Observed 119 pack-qualified event kinds; 19 have reviewed mapping support. The bank has 17 rules.
309 supported event occurrences, of which 122 have their own visible tokens; the remainder are explicit silent source-history annotations.

| World | Stories | Tokens | Event kinds | Mappable kinds |
|---|---:|---:|---:|---:|
| rescue | 20 | 2609 | 13/13 | 1 |
| kite | 20 | 1884 | 13/13 | 3 |
| key | 20 | 1950 | 13/13 | 2 |
| music | 20 | 1894 | 16/16 | 3 |
| greenhouse | 20 | 2601 | 17/17 | 2 |
| library | 20 | 2633 | 21/21 | 4 |
| pottery | 20 | 2506 | 26/26 | 4 |

## Receiving-world demonstration

Ada fetched the tape from the bench. She used the tape to repair the book. She placed the book on the bench.

The target starts with Ada holding a torn paper book, tape on a reachable bench, and explicit paper-repair capabilities. No source event IDs are chosen. The demonstration supplies the operation filters fetch → repair → put and binds the worker to Ada; the final put also binds the item to the book.
Memory is queried again after each commit. Repair is infeasible before fetching and feasible afterward. The final book is repaired and on the bench. This is an annotated-memory retrieval demonstration, not automatic plot invention.

## Additional target operations

These use a separate underdefined craft setup with explicitly declared wet clay, shaping tool, practiced drummer, support-preparation capability, broken repairable tap and drawing materials/ability.

Ada used the shaping rib to shape the cup.

Source references: pottery event 3 (silent).

Ada played the drum.

Source references: music event 7 (visible).

Ada fetched the ladder from the bench. Ada steadied the ladder.

Source references: rescue event 3 (visible).

Ada fixed the tap.

Source references: greenhouse event 8 (visible).

Ada held the atlas. Ada used the pencil to sketch the moon on the paper.

Source references: library event 17 (visible).

## Intact source examples

First seed (3000) from each world, chosen before generation. Linked JSON includes token candidates, separate historical observations, and mapping references. The prose is not split into replacement snippets.

### rescue

Sam wanted to eat the bread, but a puppy shivered on a high ledge. Sam told Mum, “The puppy needs help.” Mum told Sam, “Let me climb the ladder.” Sam told Mum, “I can steady the ladder.” Sam fetched the ladder from the shed, and he steadied the ladder. Mum climbed the ladder. She lifted the puppy down. Sam carried the puppy into the cottage, and he wrapped the puppy in the warm blanket. The puppy rested in the warm blanket.

[Annotated full token stream](rescue.memory.json)

Reusable references: 3 prepare ladder (14 tokens).

### kite

Sam wanted to fly a kite, but the kite was torn. Sam said, “I would like to fix the kite.” Mum said, “The paper is thin.” Sam told Mum, “Let me cover the tear.” Using the tape, he covered the tear. He launched the kite in the wind, but the paper tore again. Sam said, “I want to make a sail.” Mum cut a small sail from the kite with the scissors. Sam tied the sail to the boat with the string. He placed the boat on the pond. Sam and Mum watched the boat. The boat sailed across the pond.

[Annotated full token stream](kite.memory.json)

Reusable references: 4 fetch tape (silent boundary), 5 mend (9 tokens), 8 fetch scissors (silent boundary).

### key

Sam wanted to read a storybook inside, but the door was locked. The key was missing. Mum said, “I could help you.” Sam told Mum, “I would like to locate the key.” He fetched the lantern from the porch. Using the lantern, he found the key under the bench. He unlocked the door with the key. He stepped inside the cottage. He hung the key on the hook. Sam opened the storybook beside Mum.

[Annotated full token stream](key.memory.json)

Reusable references: 4 fetch light (8 tokens), 7 hang key (8 tokens).

### music

Nia borrowed the little drum from Dalia, and she hoped to play a duet with Mateo. Nia said, “I need an answering beat.” Mateo told Nia, “I am not ready for the audience.” Nia said, “I'll perform a solo.” Nia rehearsed a soft beat and a loud beat. Nia played the solo on the little drum before Dalia. Mateo clapped. Nia bowed.

[Annotated full token stream](music.memory.json)

Reusable references: 2 borrow (18 tokens), 7 perform (11 tokens), 9 return (silent boundary).

### greenhouse

Nia wanted to water the sunflower, but the tomato seedlings were thirsty. Mr Bell said, “The tap is broken.” The rain barrel held one can of water. Nia told Mr Bell, “I want to water the sunflower first.” Using the watering can, she watered the sunflower. The shade cloth fell. The tomato seedlings had a brown leaf. Nia secured the umbrella above the tomato seedlings with the garden tie. Mr Bell fixed the tap. Nia watered the tomato seedlings with water from the tap. Mrs Okafor fixed the shade cloth with the clip. Nia said, “I promise I'll water the tomato seedlings first tomorrow.” The brown leaf remained under the repaired shade cloth.

[Annotated full token stream](greenhouse.memory.json)

Reusable references: 8 repair tap (6 tokens), 12 return (silent boundary).

### library

Mina held a moon atlas. She wanted to sketch the moon. Jun said, “My whale book is missing.” Mina told Jun, “I promise to help you.” Mina and Jun searched the window nook, but Mina did not locate the whale book. Jun noticed the star bookmark on the high shelf. Ms Alvarez reserved the moon atlas for Mina. Using the ladder, Ms Alvarez lifted the whale book down. Ms Alvarez handed Jun the whale book. Jun said, “I can help you.” Jun opened the moon atlas for Mina. Mina sketched the moon from the moon atlas on the paper. Mina showed Jun the moon drawing.

[Annotated full token stream](library.memory.json)

Reusable references: 3 borrow (silent boundary), 4 place atlas (silent boundary), 15 return trolley (silent boundary), 17 sketch moon (12 tokens).

### pottery

Bea said, “I want to give Grandpa Len a cup.” The cup's handle was wide because Grandpa Len's hand was stiff. The shaping rib slipped. The cup was dented. Mr Ivo said, “The cup's wall is thick.” Grandpa Len said, “I could hold a bowl with two hands.” Bea said, “I would like a thumb rest.” Using the sponge, Bea shaped the dent into a thumb rest. Mr Ivo fired the cup twice. The cup was cool. Bea handed the cup to Grandpa Len. Grandpa Len poured tea into the cup. Grandpa Len's thumb rested in the thumb rest.

[Annotated full token stream](pottery.memory.json)

Reusable references: 3 shape (silent boundary), 9 return rib (silent boundary), 10 return sponge (silent boundary), 22 give (8 tokens).

## Limits and inspection findings

Unsupported events remain fully annotated and searchable. Matching an operation pattern is not permission to replay source state changes: target kinds, capabilities, live guards and replay must all pass.
The seven source texts are unchanged, so their existing narrative strengths and defects are unchanged. The target demonstration is a short action sequence without a developed premise/turn. No Luna quality improvement is claimed.
Token-local syntax labels and mention resolution retain the known embedded-object/nominal-place limitations. Historical after-state is explicitly source memory, never a target prefix observation.
Compound resource changes (watering), consent, reservations and many endings remain unsupported for portable execution; they are not reduced to simpler transfers merely to raise coverage.
