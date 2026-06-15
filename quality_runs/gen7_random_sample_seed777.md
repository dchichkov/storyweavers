# Gen7 Random Quality Sample - seed 777 comparison set

> Note: gen7 does not currently have a `quality.py`-style sampler. This file uses
> the same five story IDs as `gen6_random_sample_seed777.md`, generated with
> `gen7.generate(...)`, so the two samples can be compared directly.

Generation command shape:

```bash
/opt/homebrew/bin/python3.12 - <<'PY'
import gen7
for story_id in ["data00:18697", "data00:29975", "data00:36222", "data00:36242", "data00:46773"]:
    row = gen7.load_story(story_id)
    print(story_id, gen7.generate(row["kernel"]))
PY
```

Manual grading follows `QUALITY.md` dimensions, each scored 1-5.

## Aggregate

| Metric | Value |
|---|---:|
| Stories | 5 |
| Mean grammar | 4.0 |
| Mean coherence | 3.8 |
| Mean fidelity | 3.6 |
| Mean completeness | 3.6 |
| Mean naturalness | 3.4 |
| Mean overall | 3.6 |
| Usable rate | 5/5 = 100% |

## Scores

| ID | Grammar | Coherence | Fidelity | Completeness | Naturalness | Overall | Usable | Main defects |
|---|---:|---:|---:|---:|---:|---:|---|---|
| data00:18697 | 4 | 4 | 4 | 4 | 4 | 4 | yes | mild generic_label |
| data00:29975 | 4 | 4 | 3 | 3 | 3 | 3 | yes | dropped_content |
| data00:36222 | 4 | 4 | 4 | 4 | 4 | 4 | yes | mild compression |
| data00:36242 | 4 | 3 | 3 | 3 | 3 | 3 | yes | wrong_subject, dropped_content |
| data00:46773 | 4 | 4 | 4 | 4 | 3 | 4 | yes | mild generic_scene |

## 1. data00:18697

Summary: A little girl who was feeling sad and alone found comfort in a friendly barrel who listened to her worries and offered to be there for her whenever she needed to talk.

Generated:

> Once upon a time, there was a sad lonely girl. There was also a friendly kind barrel. Girl felt sad. She met Barrel. Barrel asked Girl about why she was sad. Girl shared the worries. Barrel listened carefully. Barrel made a promise. Girl felt relieved. Girl and Barrel said goodbye with a smile.

Original:

> Once upon a time, there was a little girl who was very sad and started to weep. She felt all alone and was having a hard time finding peace.
>
> Suddenly, a friendly barrel appeared in front of her. It was light brown with white paint. He asked her why she was so sad and she told him all about her worries.
>
> The friendly barrel listened very attentively and decided he wanted to help her. He told her that if she was ever feeling alone or down, she should talk to him.
>
> The little girl was so relieved to have a friend like the friendly barrel, who was always there to talk to her. She smiled and hugged the barrel until all her worries were gone.
>
> The little girl thanked the friendly barrel, who was always friendly and kind, and they both went their separate ways with a smile on their faces.

Notes: Gen7 preserves the emotional arc and avoids the gen6 pronoun/object collapse. The remaining rough edge is that `Girl` and `Barrel` still read like labels rather than natural references.

## 2. data00:29975

Summary: A tired turkey finds a cozy spot to rest but is disturbed by children playing. The children catch him and take him home, where they give him food and a warm place to sleep, making the turkey happy to have made new friends.

Generated:

> Once upon a time, there was a tired turkey. There were also kind children. Turkey rested for a while. Children played happily. A loud noise interrupted the moment. Children tried to catch Turkey. Children were kind. Turkey felt happy. Turkey felt rested. Turkey and Children became good friends.

Original:

> Once upon a time, there was a turkey who was very tired. He had been walking all day and wanted to rest. He found a cozy spot under a tree and closed his eyes.
>
> Suddenly, he was disturbed by a loud noise. It was a group of children playing nearby. The turkey tried to go back to sleep, but the noise was too much.
>
> Just when the turkey thought he couldn't take it anymore, the children noticed him. They were surprised to see a turkey so close to their playground. They decided to catch him and take him home.
>
> The turkey was scared, but the children were very kind. They gave him some food and a warm place to sleep. The turkey was no longer tired, and he was happy to have made new friends.

Notes: Gen7 is coherent and readable, but it compresses away the take-home/feed/warm-place details that carry the original resolution.

## 3. data00:36222

Summary: Lily finds a magic rock that can make things shrink and uses it to play with her dog Max, but accidentally shrinks him. They discover a secret room underground and help a mouse who is stuck there, using the magic rock to make him big again. They become friends and play together every day.

Generated:

> Once upon a time, there was a little curious playful girl named Lily. There was also a loyal playful dog named Max. There was also a worried mouse. Lily found the rock. Max became small. Lily and Max went underground. She dug carefully. She found the secret room. Lily and Max felt happy. She met Mouse. Mouse felt worried. Mouse grew big again. Mouse, Lily, and Max shared a warm hug. Lily, Max, and Mouse became good friends. Every day, the friends played together.

Original:

> Once upon a time, a girl named Lily found a magic rock. The rock could make things shrink. Lily loved to play with her new toy. One day, she was playing with her dog, Max, and she made him shrink. Max was now very small.
>
> "Max, let's go play underground," Lily said. They went to a hole in the ground and started to dig. They found a secret room underground. Lily and Max were very happy to find this new place.
>
> In the room, they saw a worried little mouse. The mouse said, "Please help me! I'm stuck in this room." Lily used the magic rock to make the mouse big again. The mouse was so happy, he gave Lily and Max a big hug. They all became good friends and played together every day.

Notes: Strong gen7 result: role preservation, causality, and the object/state trace are mostly intact. The prose is still compressed and omits some explicit dialogue/causal explanation.

## 4. data00:36242

Summary: Lily loves her new jacket with a tough zipper and wants to jump in puddles, but her mom won't let her. They compromise and go home to put on rain boots and jump in puddles together.

Generated:

> Once upon a time, there was a little playful stubborn girl named Lily. There was also a caring protective mother. Every day, Lily loved to jump. Mom tried to keep the jacket dry. Lily resisted. Mom agreed. She wore the rainboots. Lily and Mom felt happy. Mom found a compromise. She learned that working together helped.

Original:

> Once upon a time, there was a little girl named Lily. She loved playing outside and jumping in puddles. One day, Lily's mom bought her a new jacket with a tough zipper. Lily loved her new jacket and wore it everywhere she went.
>
> One rainy day, Lily and her mom went to the park. Lily wanted to jump in the puddles, but her mom said no. "You'll get your new jacket wet," her mom said. Lily didn't want to listen and tried to run towards the puddles, but her mom grabbed her hand and said, "You have to resist the urge to jump in the puddles today."
>
> Lily pouted and crossed her arms. "But I want to jump in the puddles!" she said. Her mom smiled and said, "How about we go home and put on our rain boots and jump in the puddles together?" Lily's face lit up and she hugged her mom. "Yay, let's do it!" she said as they walked back home to get their rain boots.

Notes: The compromise shape is visible, but the generated ending assigns the lesson to Mom and compresses the rain-boots resolution too aggressively.

## 5. data00:46773

Summary: Tim meets a bird in the park who can shoot gold from its beak, but the gold turns out to be rocks.

Generated:

> Once upon a time, there was a little curious greedy boy named Tim. There was also a playful supportive mother. There was also a magical generous bird. Tim wanted the gold. The story moved to the park. He met Bird. He traded the bread. He received the gold. The gold turned into the rocks. Mom and Tim played at the park.

Original:

> One day, a boy named Tim went to play in the dark park. He saw a big tree and wanted to climb it. As he went up, he found a little bird. The bird said, "Hi, I can shoot gold from my beak!"
>
> Tim was very happy. He asked the bird, "Can you give me some gold?" The bird said, "Yes, but I need something to eat first." Tim gave the bird some bread, and the bird shot gold on the ground.
>
> Tim took the gold home and showed his mom. But the gold turned into rocks! His mom said, "It's just a fun trick, Tim. Let's go back to the park and play some more." Tim and his mom laughed and played in the park all day.

Notes: The transaction and transformation are clear. Remaining roughness is mostly generic scene wording and missing dialogue/flavor.
