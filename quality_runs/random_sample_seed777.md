# Random Quality Sample - seed 777

> Note: this sample was produced with `quality.py`, whose current sampling
> harness uses the gen6 registry/generator. It is not a gen7 output sample.

Sample command:

```bash
.venv/bin/python quality.py --sample -n 5 --seed 777 --scan 80000 --out /private/tmp/storyweavers_random_quality_sample.jsonl
```

Manual grading follows `QUALITY.md` dimensions, each scored 1-5.

## Aggregate

| Metric | Value |
|---|---:|
| Stories | 5 |
| Mean coverage ratio | 0.932 |
| Mean grammar | 2.6 |
| Mean coherence | 2.6 |
| Mean fidelity | 3.2 |
| Mean completeness | 3.0 |
| Mean naturalness | 2.4 |
| Mean overall | 2.6 |
| Usable rate | 1/5 = 20% |

## Scores

| ID | Coverage | Grammar | Coherence | Fidelity | Completeness | Naturalness | Overall | Usable | Main defects |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| data00:18697 | 8/8 | 3 | 3 | 4 | 4 | 3 | 3 | no | pronoun_error, wrong_subject, naturalness |
| data00:29975 | 6/8 | 2 | 2 | 3 | 2 | 2 | 2 | no | wrong_subject, clause_in_noun_slot, article_error |
| data00:36222 | 13/13 | 2 | 2 | 3 | 3 | 2 | 2 | no | wrong_subject, clause_in_noun_slot, literal_concept |
| data00:36242 | 10/11 | 2 | 2 | 2 | 2 | 2 | 2 | no | dropped_content, literal_concept, wrong_subject |
| data00:46773 | 5/5 | 4 | 4 | 4 | 4 | 3 | 4 | yes | mild dropped_content |

## 1. data00:18697

Coverage: 8/8 (1.0)

Summary: A little girl who was feeling sad and alone found comfort in a friendly barrel who listened to her worries and offered to be there for her whenever she needed to talk.

Generated:

> Once upon a time, there was a sad lonely person named Girl. There was also a friendly kind person named Barrel. Girl felt sad. They came across Barrel. Barrel spoke up. Girl shared the worries. Barrel listened carefully. They made a promise. Girl felt a wave of relief. They hugged Barrel. They smiled. They had to part from Barrel and the smile.

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

Notes: Preserves the emotional arc, but "Girl" as a name, repeated "They", and the final "part from Barrel and the smile" make it feel templated.

## 2. data00:29975

Coverage: 6/8 (0.75)

Summary: A tired turkey finds a cozy spot to rest but is disturbed by children playing. The children catch him and take him home, where they give him food and a warm place to sleep, making the turkey happy to have made new friends.

Generated:

> Once upon a time, there was a tired bird named Turkey. There was also a kind group named Children. Turkey rested for a while. Children played happily with Children. Children was disturbed by the noise and Children. Turkey felt attempt sleep. Children felt capture attempt. They fed the animals. They warmed place. Turkey felt happy. Turkey and Children became good friends.

Original:

> Once upon a time, there was a turkey who was very tired. He had been walking all day and wanted to rest. He found a cozy spot under a tree and closed his eyes.
>
> Suddenly, he was disturbed by a loud noise. It was a group of children playing nearby. The turkey tried to go back to sleep, but the noise was too much.
>
> Just when the turkey thought he couldn't take it anymore, the children noticed him. They were surprised to see a turkey so close to their playground. They decided to catch him and take him home.
>
> The turkey was scared, but the children were very kind. They gave him some food and a warm place to sleep. The turkey was no longer tired, and he was happy to have made new friends.

Notes: The broad plot survives, but subjects and clauses degrade badly: "Children was disturbed", "felt attempt sleep", and "warmed place".

## 3. data00:36222

Coverage: 13/13 (1.0)

Summary: Lily finds a magic rock that can make things shrink and uses it to play with her dog Max, but accidentally shrinks him. They discover a secret room underground and help a mouse who is stuck there, using the magic rock to make him big again. They become friends and play together every day.

Generated:

> Once upon a time, there was a little curious playful girl named Lily. There was also a loyal playful dog named Max. There was also a worried mouse named Mouse. Lily finally found the rock. The rock sparkled with magic. Max shrank down. Lily wanted Lily and Max. Lily dug the ground. Lily discovered the secretroom. There was great joy over Lily and Max. Mouse came across Mouse. Mouse seemed worried. They pleaded with someone. They grew. They got a warm hug. Everyone became good friends. Every day, Lily had the same routine. There was lots of fun.

Original:

> Once upon a time, a girl named Lily found a magic rock. The rock could make things shrink. Lily loved to play with her new toy. One day, she was playing with her dog, Max, and she made him shrink. Max was now very small.
>
> "Max, let's go play underground," Lily said. They went to a hole in the ground and started to dig. They found a secret room underground. Lily and Max were very happy to find this new place.
>
> In the room, they saw a worried little mouse. The mouse said, "Please help me! I'm stuck in this room." Lily used the magic rock to make the mouse big again. The mouse was so happy, he gave Lily and Max a big hug. They all became good friends and played together every day.

Notes: Fully covered but still not very readable. Strong signs of wrong subject selection: "Mouse came across Mouse", "They grew", "They got a warm hug".

## 4. data00:36242

Coverage: 10/11 (0.909)

Summary: Lily loves her new jacket with a tough zipper and wants to jump in puddles, but her mom won't let her. They compromise and go home to put on rain boots and jump in puddles together.

Generated:

> Once upon a time, there was a little playful stubborn girl named Lily. There was also a caring protective mother named Mom. Every day, Lily had the same routine. There was the puddles. She had. There was a disagreement. She resisted. Mom put on the rainboots. There was the puddles and the together. In the end, Lily and Mom felt full of joy. Mom realized that everyone worked together.

Original:

> Once upon a time, there was a little girl named Lily. She loved playing outside and jumping in puddles. One day, Lily's mom bought her a new jacket with a tough zipper. Lily loved her new jacket and wore it everywhere she went.
>
> One rainy day, Lily and her mom went to the park. Lily wanted to jump in the puddles, but her mom said no. "You'll get your new jacket wet," her mom said. Lily didn't want to listen and tried to run towards the puddles, but her mom grabbed her hand and said, "You have to resist the urge to jump in the puddles today."
>
> Lily pouted and crossed her arms. "But I want to jump in the puddles!" she said. Her mom smiled and said, "How about we go home and put on our rain boots and jump in the puddles together?" Lily's face lit up and she hugged her mom. "Yay, let's do it!" she said as they walked back home to get their rain boots.

Notes: The happy compromise is barely present; several lines are fragments ("She had", "the puddles and the together").

## 5. data00:46773

Coverage: 5/5 (1.0)

Summary: Tim meets a bird in the park who can shoot gold from its beak, but the gold turns out to be rocks.

Generated:

> Once upon a time, there was a little curious greedy boy named Tim. There was also a playful supportive mother named Mom. There was also a magical generous bird named Bird. Tim wanted gold. The gold turned into the rocks. Tim traded the bread. He received the gold. In the end, Mom and Tim played together.

Original:

> One day, a boy named Tim went to play in the dark park. He saw a big tree and wanted to climb it. As he went up, he found a little bird. The bird said, "Hi, I can shoot gold from my beak!"
>
> Tim was very happy. He asked the bird, "Can you give me some gold?" The bird said, "Yes, but I need something to eat first." Tim gave the bird some bread, and the bird shot gold on the ground.
>
> Tim took the gold home and showed his mom. But the gold turned into rocks! His mom said, "It's just a fun trick, Tim. Let's go back to the park and play some more." Tim and his mom laughed and played in the park all day.

Notes: Best of this batch. It drops the bird dialogue and tree/climb setup, but the trade, gold-to-rocks twist, and play ending are coherent.
