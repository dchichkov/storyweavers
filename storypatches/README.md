# Storypatches

An isolated authoring experiment, restarted around supplied gen6 kernels.

## Current workflow: kernel → story + QA

`kernel_author.py` is the active entry point. Supply one gen6 kernel; Qwen returns
one JSON object containing `title`, `story`, and `qa` (question/answer pairs).
There is one model call for both prose and QA. The kernel is supplied verbatim,
with no randomly selected words, genres, ATU types, outlines, or section quotas.
The example story below is a human reference, not prose pasted into the model's
prompt. Bare emotions/actions should be expressed through the current physical
character, and explicit roles and event order must be preserved.

```bash
./.venv/bin/python -m storypatches.kernel_author \
  --kernel storypatches/examples/lily.kernel \
  --out storypatches/runs/my_kernel_story
```

Defaults use the local Qwen server at `http://127.0.0.1:8001/v1`, with thinking
disabled. `--thinking` enables it; `--questions` defaults to three. `--dry-run`
saves the request without inference. A dry run can be continued with the same
command without that flag. Saved responses can be reused; interrupted requests
are not automatically reissued. Changed input or settings require a new run dir.

Artifacts: `kernel.txt`, `story.json`, readable `story.md`, frozen request and
response, settings, token usage, and structural validation status. Input is
parsed as a restricted declarative AST and checked against `gen6registry` for
unregistered explicit calls; it is never executed as Python. The gen6 engine and
its classical runtime are unchanged. Unregistered names are reported, not silently
claimed to be implemented. Structural checks do **not** prove semantic fidelity;
read the kernel, story, and answers together before expanding this experiment.

```bash
./.venv/bin/python -m unittest storypatches.test_kernel_author
```

### First kernel-first sample

Local Qwen generated [Lily, the Dog, and the Pink Eraser](runs/kernel_lily_20260911_thinking/story.md)
from the example kernel with `--thinking`: 515 story words and three QA pairs.
The saved JSON, request, response, and usage are in the same directory.
Manual review: Mom finds and returns the eraser, Lily is grateful, Mom's warning
follows the teasing, and the ending shows changed behavior. Remaining defects:
the eraser supposedly bounces from the kitchen table to the living-room couch
without a plausible connection; QA adds Lily "standing over" the dog although
that position was not established. This is a baseline, not a semantic quality pass
or a Terra-graded result. A cached-response rerun and four unit tests pass.

Next stage: a deliberate edit must update the kernel, prose, and any affected QA
together. For Mom's resignation example, changing only dialogue would leave the
kernel's `Angry`/`Anger` inconsistent. Choose or implement the appropriate gen6
state representation first, then generate the diff against the exact saved
bundle. No new patch batch or random patch composition is part of this first step.
The previous pipeline and its runs remain below as historical experiments.



## Initial raw story production

The following story supplied as an example of producing a story from a kernel.
given the kernel
--
Lily(Character, girl, Curious)
Fear(Lily, dog) + Brave(Lily) + Mock
Happy

Mom(Character, mother, Angry)
Warning(Mom, Lily) + Anger

Vanish(eraser) + Loss(Lily, eraser) + Search(Lily, eraser)
Find(Mom, eraser, location=couch) + Return(eraser, Lily)
Joy(Lily) + Gratitude(Lily, object=Mom)
Lesson(Lily)
--

Model should produce a json with the story and set of QA:

One afternoon, Lily, a curious girl who had just turned nine, saw a big dog near the sidewalk. For a moment, she was afraid, but she was also curious about the dog, so she came a little closer.
The dog ignored her.
Lily came even closer and stuck out her tongue at the dog, just to see what it would do.
The dog looked at her but still did nothing.
Now Lily felt much braver. She decided that the dog wasn't scary after all, so she stuck out her tongue again.
“Nya-nya ny-nya nyaaaa-nya!”
Then she laughed and ran home, very pleased with herself.
When Lily got home, she told Mom all about the dog. She explained how frightened she had been at first, how she had walked closer, and how the dog had done nothing even when she stuck out her tongue at it.
“And then I did this!” Lily said proudly.
She stuck out her tongue at Mom.
“Nya-nya ny-nya nyaaaa-nya!”
Mom wasn't amused.
“Lily, that's rude,” she said. “And you shouldn't tease animals either. That dog may have ignored you today, but another dog might not. You need to think before you do things like that.”
Lily didn't think Mom's warning was very important. She was still excited about her adventure, so she ran away laughing. At the doorway, she turned around and stuck out her tongue once more.
“Nya-nya ny-nya nyaaaa-nya!”
“Lily!” Mom called after her, now angry. “You really need to learn to listen!”
But Lily had already run into the living room.
A little later, she sat down on the couch to do her homework. At first she worked quietly, but soon she became bored. She picked up her eraser and began tossing it into the air.
Up it went.
Down it came.
Lily caught it.
She tossed it again, this time a little higher.
Mom walked past and saw what Lily was doing.
“Don't play with your eraser like that,” Mom warned her. “You're going to lose it.”
“I won't!” Lily said.
She tossed the eraser again.
This time it hit the edge of her hand, bounced across the couch, and disappeared.
Lily stopped smiling.
She looked beside her notebook.
Nothing.
She looked under the couch.
Nothing.
She searched her backpack, under the table, behind the chair, and even inside her shoes.
The eraser was nowhere to be found.
“Mom!” Lily called. “My eraser vanished!”
Mom came into the room.
“What happened?”
“I don't know,” Lily said. “I was just playing with it, and then it disappeared.”
Mom frowned.
“I warned you that you might lose it.”
Lily looked down. Mom was right, and now Lily needed the eraser to finish her homework.
Still, Mom helped her look.
They searched beneath the table and behind the furniture. Lily crawled around on the floor while Mom checked the places Lily had already searched.
Finally, Mom lifted one of the couch cushions.
“There it is.”
The eraser had slipped deep into the gap between the cushions.
Mom picked it up and handed it to Lily.
Lily's face brightened.
“My eraser!”
She hugged Mom.
“Thank you, Mom.”
Mom smiled a little.
“Maybe next time you'll listen when I warn you.”
Lily looked at the eraser in her hand and thought about the dog, Mom's warnings, and all the searching they had just done.
“I think I will,” she said.
And this time, she didn't stick out her tongue.
Question 1: Why did Lily come closer to the dog even though she was afraid?
Answer: Lily came closer because she was curious about the dog and wanted to see what it would do.
Question 2: Why did Lily lose her eraser?
Answer: Lily lost her eraser because she ignored Mom's warning and kept tossing it into the air. It bounced away and fell between the couch cushions.
Question 3: Why was Mother grateful?
Answer: Mother wasn't grateful in the story. Lily was grateful to her mother because Mom helped her search for the lost eraser, found it in the couch, and returned it to her.


## Patches production

```
--- lily_story_original.txt
+++ lily_story_resignation.txt
@@ -26,18 +26,19 @@
 She stuck out her tongue at Mom.
 
 “Nya-nya ny-nya nyaaaa-nya!”
 
-Mom wasn't amused.
+Mom sighed.
 
 “Lily, that's rude,” she said. “And you shouldn't tease animals either. That dog may have ignored you today, but another dog might not. You need to think before you do things like that.”
 
 Lily didn't think Mom's warning was very important. She was still excited about her adventure, so she ran away laughing. At the doorway, she turned around and stuck out her tongue once more.
 
 “Nya-nya ny-nya nyaaaa-nya!”
 
-“Lily!” Mom called after her, now angry. “You really need to learn to listen!”
+Mom shook her head and sighed again.
+
+“Someday you might actually listen to me,” she said, mostly to herself.
 
 But Lily had already run into the living room.
 
 A little later, she sat down on the couch to do her homework. At first she worked quietly, but soon she became bored. She picked up her eraser and began tossing it into the air.
@@ -69,11 +70,12 @@
 “Mom!” Lily called. “My eraser vanished!”
 
 Mom came into the room.
 
 “What happened?”
 
 “I don't know,” Lily said. “I was just playing with it, and then it disappeared.”
 
-Mom frowned.
+Mom looked at Lily for a moment and let out a weary sigh.
 
 “I warned you that you might lose it.”
 
 Lily looked down. Mom was right, and now Lily needed the eraser to finish her homework.
@@ -95,16 +97,16 @@
 She hugged Mom.
 
 “Thank you, Mom.”
 
-Mom smiled a little.
+Mom gave her a tired little smile.
 
 “Maybe next time you'll listen when I warn you.”
 
 Lily looked at the eraser in her hand and thought about the dog, Mom's warnings, and all the searching they had just done.
 
 “I think I will,” she said.
 
 And this time, she didn't stick out her tongue.
 
 ### Questions and Answers
 
-**Question 1: Why did Mom become angry with Lily?**
-**Answer:** Mom became angry because Lily ignored her warning and teased her by sticking out her tongue. Later, Lily ignored another warning and kept playing with her eraser.
+**Question 1: Why did Mom react with resignation when Lily ignored her?**
+**Answer:** Mom reacted with resignation because she had already warned Lily, but Lily ignored her and teased her by sticking out her tongue again. Instead of becoming angry, Mom sighed and seemed to expect that Lily would have to learn from her own mistake.
 
 **Question 2: Why did Lily lose her eraser?**
 **Answer:** Lily lost her eraser because she ignored Mom's warning and kept tossing it into the air. It bounced away and fell between the couch cushions.
 
 **Question 3: Why was Mother grateful?**
 **Answer:** Mother wasn't grateful in the story. Lily was grateful to her mother because Mom helped her search for the lost eraser, found it in the couch, and returned it to her.
```



## Outdated / failed


1. a deterministic seed selects three required CHILDES words, 3–5 compatible
   kernels, a beginning, ending, basic plot, ATU type, genre, situation, and
   location;
2. Luna/Flex writes an outline, six-section story, and grounded conversational
   Q&A;
3. Luna produces 100 independent edits through one synthetic OpenAI custom text
   tool named `apply_patch`;
4. local code applies compatible sets of 3–5 patches to make 100 unique variants;
5. deterministic QA checks and the existing Terra story-set judge evaluate them.

Patch calls have no read, write, shell, or search tools. Each call receives the
complete base bundle in a stable cached prefix and must finish with one
`apply_patch` tool call. The tool only returns text; `storypatches` parses,
validates, and applies it locally. OpenCode is neither imported nor invoked.
Source matching first uses exact text, then permits curly/straight quote
equivalence only when it identifies one unique match. Other text differences
remain errors; raw model patches are retained for inspection.
Multiple update sections for a file are applied in order within the atomic patch.

An initial local run with three stories, 100 patches per story, and 100 variants
per story is available in [runs/qwen_three_20260909_v2/](runs/qwen_three_20260909_v2/README.md).

## Setup and tests

From the repository root:

```bash
./.venv/bin/pip install -r storyscenes/requirements-authoring.txt
./.venv/bin/python -m unittest storypatches.test_storypatches
```

## Inspect requests without an API call

```bash
./.venv/bin/python -m storypatches.pipeline \
  --out storypatches/runs/dry_run --seed 42 --count 2 --dry-run
```

## Author with OpenAI and evaluate

This makes at least 103 paid Luna calls per base story: outline, prose,
conversations, and 100 patches. Known-invalid returned patches may use a bounded
replacement call. The first patch request warms the explicit 30-minute cache;
the rest share exactly the same prefix and cache key.

```bash
OPENAI_API_KEY=... ./.venv/bin/python -m storypatches.pipeline \
  --out storypatches/runs/trial_01 \
  --campaign storypatches/campaigns/trial_01 \
  --seed 42 --count 1 --variants 100 --evaluate
```

Use `--api-key-file PATH` instead of the environment variable if needed.
`--cache-mode legacy` is available for clients/models without explicit cache
breakpoints. There is no automatic fallback after a dispatched request.

## Debug with local Qwen

For a local OpenAI-compatible Responses endpoint, the pipeline appends `/v1`
when it is absent, does not require an API key, and omits OpenAI-only Flex,
reasoning, and prompt-cache fields:

```bash
./.venv/bin/python -m storypatches.pipeline \
  --base-url http://127.0.0.1:8001/ \
  --model Qwen/Qwen3.8-27B-FP8 \
  --fast-patches --patch-attempts 3 \
  --out storypatches/runs/qwen_debug \
  --seed 42 --count 1 --variants 100
```

Local Qwen uses a standard `apply_patch` function tool with a single `patch`
string argument, because the tested server advertises custom text tools but
returns those calls as prose. The patch syntax and local validation are the same.
Qwen receives the JSON schema in the prompt as well as the response format.
Thinking is disabled for base artifacts and enabled with a larger token allowance
for patches by default. `--fast-patches` tries two non-thinking patch attempts
first, then falls back to reasoning. These settings use vLLM's
`chat_template_kwargs` extension.
Custom endpoints default to `--cache-mode off`; override
it only if the server implements the corresponding cache fields. The server
must support strict JSON-schema output and function tool calls as well as the
Responses route. A Chat-Completions-only endpoint is not sufficient.

Use `--dry-run` with the same endpoint/model flags to inspect requests without
performing inference. Local model usage is recorded in the artifact ledger, but
its cost is reported as unpriced.

An interrupted request leaves its request file without a response and is not
silently retried. Put an empty `STOP` file in the run directory to block new
dispatches. Outputs include every frozen request/response, base bundle, patch
attempt, accepted patch, conflict graph, variants, QA metrics, token cost, and
evaluation artifacts.
