# Compositional Microdrama: The Palace That Learned to Read

Proof of concept, 24 October 2026. Adapted from the two user-supplied stories of
G. Wolf, the Three Little Pigs, and Story Fox. All implementation stays here.

## Acceptance requirements

1. Run without models, network, third-party packages, or imports from sibling
   experiments. Provide readable generated stories, traces, and reproduction commands.
2. Preserve the inspiration's causal spine: material failures become a false
   accusation; propaganda survives exile; occupation and coerced building benefit
   the pigs; Fox redirects their prestige toward books; practical learning can
   undermine the rulers' account of who built the village.
3. Treat books, posters, people, and encounters as carriers of composable weighted
   content. Unembedded content has no influence. Transmission requires contact;
   attention dilutes it. False public belief never overwrites physical truth.
4. Compose bounded encounters through world conditions, with local alternatives,
   optional/interleavable encounters, consequential choices, and different endings.
   No parameter directly selects the ending. Do not count ordering or wording
   changes as new plots.
5. Keep ownership separate from occupation, track physical access to books, and
   require observed practice before claiming skill. No instant enlightenment or
   unexplained restoration of the cottage.
6. Separate execution from narration. Narrative paragraphs must describe committed
   events and end with a physical image; rejected/speculative moves are silent.
7. Supply grounded QA with event references and contextual follow-ups. Distinguish
   what the world knows, what a character believes, and what the reader is told.
8. Verify rollback, composition, transmission, counterfactuals, replay, all finite
   parameter combinations, and unfiltered seeded examples. Read outputs manually;
   tests alone are not a literary evaluation.

## What is borrowed

- `story.py` / gen6: additive content and attention division, physical carriers,
  accumulated magnitudes, compatible actions. Here a `Memeplex` can contain a
  concept, character, action, or whole named narrative. Executable operations
  remain a separate layer; this does not implement every aspect of the full algebra.
- Storypatches: atomic changes, exact preconditions, provenance, and stable-base
  rejection. We patch structured state, not already-written English.
- StoryScenes: local scenes sharing persistent state, conditional scene admission,
  atomic transitions, state-dependent endings, and counterfactual comparisons.
- StoryWorlds: character-specific values, enacted physical affordances, dialogue
  with consequences, and trace-grounded QA.
- Alabaster: facts, topics, and follow-up context; mood and knowledge are distinct.
- Versu: opportunities offered by social situations; character state determines
  which available response is taken. This is a small explicit policy, not a
  reconstruction of its autonomous-agent architecture.
- Counterfeit Monkey / Inform: reusable operations plus a curated content library,
  physical prerequisites, and understandable failure cases.
- STORYBOOK / Curveship: separate discourse planning, selective narration, and
  causal/temporal links. Literary language is authored at encounter scale here;
  there is no general English grammar or arbitrary viewpoint transformation.

## Story-first outline

Begin with a sound cottage and a weak straw house. A gust supplies the first
accusation; a poster outlives its speaker. Wolf leaves with his soup pot. Rain
and bad brickwork give the pigs further occasions to repeat their story, then
take his cottage. They bring him back to build the village they claim as theirs.

Fox steals cheese and notices that everybody looks for the pictured wolf. A
piglet may witness the theft; the observation changes that piglet's belief without
magically persuading everyone. Fox uses the whispered name Three Little Wolves
to make the creek cottage intolerable to its occupants. They commission a palace
and buy books. Their intention is distinction, not education.

The books arrive as material things. Open shelves permit reading; locked cupboards
do not. Reading and teaching supply different strengths of knowledge. Piglets
test a drain and a bridge. A wet footprint or a plank remaining level proves a
local result. Working together also builds a shared identity. A borrowed book
can be physically carried to another reader; knowledge never teleports.

At the opening the pigs order the books removed. Piglets with practical reasons
to keep them can object. Enough capable piglets with shared experience can act
together, inducing the prestige-conscious pigs to retreat. They explicitly
relinquish occupation of Wolf's cottage. The palace becomes a library, and Wolf
returns to light his stove. If knowledge survives in only one reader, one book
leaves for a small private school. If nobody can use the books, the rulers lock
them away. The final image must show the difference.

## Limits planned into the experiment

One adapted fable with a finite encounter library and three possible institutional
outcomes. Numerical thresholds are authoring choices, not a validated psychology
or political model. A successful resistance is specific to this fictional cast,
not a general claim about how oppressed communities behave. No claim of cheap
mass authorship, unbiased scoring, or training-data utility follows from this POC.
