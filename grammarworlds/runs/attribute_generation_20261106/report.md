# Joint annotated-token generation

140 matched runs preserve text, physical state, QA and word probabilities with heads off.
140 runs with heads replay successfully; heads changed 150 word distributions.
These are correctness and preservation checks, not a new independent quality evaluation.

| World | Matched runs | Ambiguous selected steps | Head-changed steps | Candidate kernels seen |
|---|---:|---:|---:|---:|
| rescue | 20 | 128 | 8 | 13/13 |
| kite | 20 | 151 | 35 | 13/13 |
| key | 20 | 142 | 34 | 13/13 |
| music | 20 | 47 | 12 | 16/16 |
| greenhouse | 20 | 185 | 19 | 17/17 |
| library | 20 | 163 | 22 | 21/21 |
| pottery | 20 | 204 | 20 | 26/26 |

## Rescue — seed 7

Nora wanted to eat the bread, but a puppy shivered on a high ledge. Nora said, “The puppy needs help.” Dad said, “I can lower the basket.” Nora said, “I can share the bread.” Nora put the bread in the basket. Dad carried the basket to the window, and he lowered the basket to the ledge with the rope. Nora waited because the puppy was frightened. The puppy entered the basket, and it ate the bread. Dad lowered the basket to the garden with the rope. Nora carried the puppy into the cottage, and she wrapped the puppy in the warm blanket. Nora was hungry, but the puppy rested in the warm blanket.

[Annotated tokens](rescue.tokens.json) · [Complete joint trace](rescue.trace.json.gz)

**Q:** Why was Nora hungry at the end?  
**A:** The puppy ate the bread that Nora had meant to eat. It rested in the warm blanket after the rescue.

**Q:** What interrupted the meal?  
**A:** A puppy was shivering on a high ledge. Nora wanted to eat the bread.

Next candidates after `(scene start)`:

| Word | Scene meaning | Clause/action | Entity | Probability |
|---|---|---|---|---:|
| Dad | choose ladder | — | helper | 0.2158 |
| Dad | choose basket | — | helper | 0.7842 |

## Kite — seed 7

Nora wanted to fly a kite, but the kite was torn. Nora said, “I want to repair the kite.” Dad said, “The boat needs a sail.” Nora said, “I can cover the tear.” She covered the tear with the tape. She launched the kite in the wind. Nora and Dad watched the patched kite. The kite danced above the meadow.

[Annotated tokens](kite.tokens.json) · [Complete joint trace](kite.trace.json.gz)

**Q:** What did they watch at the end?  
**A:** Nora and Dad watched the patched kite dancing above the meadow. The tape had covered its tear.

**Q:** Who wanted to fly the kite?  
**A:** Nora wanted to fly the kite. The kite was torn.

Next candidates after `(scene start)`:

| Word | Scene meaning | Clause/action | Entity | Probability |
|---|---|---|---|---:|
| Nora | choose patch | — | hero | 0.4428 |
| Nora | choose sail | — | hero | 0.5572 |

## Key — seed 7

Nora wanted to read a storybook inside, but the door was locked. The key was missing. Dad said, “I can help you.” Nora said, “I want to find the key.” Nora fetched the lantern from the porch. She used the lantern to find the key under the bench. She unlocked the door with the key, and she stepped inside the cottage. She hung the key on the hook. Nora opened the storybook beside Dad.

[Annotated tokens](key.tokens.json) · [Complete joint trace](key.trace.json.gz)

**Q:** What changed by the end?  
**A:** Nora opened the storybook beside Dad. The found key was on the hook.

**Q:** Who wanted to read inside?  
**A:** Nora wanted to read a storybook inside. The door was locked.

Next candidates after `(scene start)`:

| Word | Scene meaning | Clause/action | Entity | Probability |
|---|---|---|---|---:|
| Nora | choose search | — | hero | 0.7380 |
| Nora | admit loss | — | hero | 0.2620 |

## Music — seed 7

Nia borrowed the little drum from Dalia, and she hoped to play a duet with Mateo. Nia said, “I need an answering beat.” Mateo said, “I am not ready for the audience.” Nia said, “I choose to perform a solo.” Nia practiced a soft beat and a loud beat. Nia performed the solo on the little drum before Dalia. Mateo clapped, and Nia bowed.

[Annotated tokens](music.tokens.json) · [Complete joint trace](music.trace.json.gz)

**Q:** How did Mateo respond after Nia played?  
**A:** Mateo clapped, and Nia bowed. Nia had performed before Dalia.

**Q:** What did Nia hope to do?  
**A:** Nia hoped to play a duet with Mateo. She borrowed the little drum from Dalia.

Next candidates after `(scene start)`:

| Word | Scene meaning | Clause/action | Entity | Probability |
|---|---|---|---|---:|
| Nia | choose solo | — | hero | 0.3951 |
| Mateo | offer pattern | — | partner | 0.2989 |
| Mateo | offer private | — | partner | 0.3060 |

## Greenhouse — seed 7

Nia wanted to water the sunflower, but the tomato seedlings were thirsty. Mr Bell said, “The tap is broken.” The rain barrel held one can of water. Nia said, “I can divide water equally.” She divided water equally between the tomato seedlings and the sunflower. The shade cloth fell. Nia secured the umbrella above the tomato seedlings with the garden tie. She moved the sunflower under the umbrella. Mr Bell said, “I promise to repair the tap tomorrow.” The tomato seedlings and the sunflower stood upright under the umbrella.

[Annotated tokens](greenhouse.tokens.json) · [Complete joint trace](greenhouse.trace.json.gz)

**Q:** How were the plants protected at the end?  
**A:** The tomato seedlings and sunflower stood under the umbrella. Nia had divided the water equally between them.

**Q:** Who wanted to water the sunflower?  
**A:** Nia wanted to water the sunflower. The tomato seedlings were thirsty too.

Next candidates after `(scene start)`:

| Word | Scene meaning | Clause/action | Entity | Probability |
|---|---|---|---|---:|
| Nia | choose seedlings | — | hero | 0.2134 |
| Nia | choose flower | — | hero | 0.5197 |
| Nia | choose share | — | hero | 0.2668 |

## Library — seed 7

Mina held a moon atlas, and she wanted to sketch the moon. Jun said, “My whale book is missing.” Mina said, “I promise to help you.” Mina and Jun searched the window nook, but Mina did not find the whale book. Jun spotted the star bookmark on the high shelf. Ms Alvarez reserved the moon atlas for Mina. Ms Alvarez used the ladder to lift the whale book down. Ms Alvarez gave Jun the whale book. Jun said, “I can help you.” Jun opened the moon atlas for Mina. Mina sketched the moon from the moon atlas on the paper. Mina showed Jun the moon drawing.

[Annotated tokens](library.tokens.json) · [Complete joint trace](library.trace.json.gz)

**Q:** Who reserved the atlas for Mina?  
**A:** Ms Alvarez reserved the moon atlas for Mina.

**Q:** How did Mina's drawing plan turn out?  
**A:** Mina showed Jun her moon drawing. Ms Alvarez had reserved the atlas for her.

Next candidates after `(scene start)`:

| Word | Scene meaning | Clause/action | Entity | Probability |
|---|---|---|---|---:|
| Jun | clue | spot | friend | 0.5000 |
| Jun | clue | see | friend | 0.5000 |

## Pottery — seed 7

Bea said, “I want to give Grandpa Len a cup.” The cup's handle was wide because Grandpa Len's hand was stiff. The shaping rib slipped, and the cup was dented. Mr Ivo said, “The cup's wall is thick.” Grandpa Len said, “I can hold a bowl with two hands.” Bea said, “I want a thumb rest.” Bea used the sponge to shape the dent into a thumb rest. Mr Ivo fired the cup twice. The cup was cool. Bea gave Grandpa Len the cup. Grandpa Len poured tea into the cup. Grandpa Len's thumb rested in the thumb rest.

[Annotated tokens](pottery.tokens.json) · [Complete joint trace](pottery.trace.json.gz)

**Q:** How did Bea use the dent after Mr Ivo checked the cup?  
**A:** Bea shaped the dent into a thumb rest with the sponge. Mr Ivo had said the cup's wall was thick.

**Q:** Where did Grandpa Len rest his thumb?  
**A:** Grandpa Len rested his thumb in the thumb rest. Bea had shaped the dent into that thumb rest.

Next candidates after `(scene start)`:

| Word | Scene meaning | Clause/action | Entity | Probability |
|---|---|---|---|---:|
| Bea | thumb | — | hero | 0.4033 |
| Bea | smooth | — | hero | 0.2965 |
| Bea | remake | — | hero | 0.3002 |

The runtime conditions on the visible word while retaining correlated attribute alternatives.
The exported per-token posterior is what was known at emission; later words can resolve it internally.
State features are from before the candidate scene commits. Scene frame roles and clause roles are distinct.
Unknown or inapplicable bindings remain explicit; no entity is invented from a matching noun.
