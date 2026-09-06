#!/usr/bin/env python3
"""
A small Storyweavers world: a comedy of coastal confusion and a very talkative
inner monologue.

Premise:
A child at the coast wants to impress others, but a tiny problem with a nostril
turns the outing into a silly, state-driven mess. The child thinks through the
problem, tries a few bad ideas, gets help, and ends with a funny, relieved
resolution.

The world model tracks:
- physical meters: windblown sand, saltwater, tissue use, distance to shelter
- emotional memes: embarrassment, worry, relief, confidence, amusement

The prose is generated from the simulated world, not a frozen template.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

HERE = Path(__file__).resolve()
ROOT = next(
    parent for parent in HERE.parents if (parent / "results.py").is_file()
)
sys.path.insert(0, str(ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402

NAME_POOL = ["Milo", "Nina", "Toby", "Luna", "Pip", "Ivy", "Theo", "Zara"]
ADJ_POOL = ["tiny", "curious", "bright-eyed", "silly", "careful", "cheerful"]
HELPER_POOL = ["mom", "dad", "a friend", "an older cousin"]
COAST_FEATURES = ["pier", "dunes", "boardwalk", "rocky shore", "shell path"]


INCIDENTS = [
    {
        "goal": "unroll a hand-drawn treasure map without letting the wind fold it",
        "premise": "had promised to lead a tiny treasure-map walk for the family",
        "problem": "a loose gull feather spun off the map and tickled one nostril",
        "failed_action": "tried to hold the map, pinch the twitchy nostril, and point grandly all at once",
        "consequence": "A sneeze sent the map flapping over a bench like a runaway tablecloth.",
        "clue": "the shell weights had rolled away from the map's corners",
        "helper_action": "set a tissue beside four flat shells and caught the map before it reached a puddle",
        "plan": "wipe the tickle away, weight every corner, and restart the treasure walk",
        "child_action": "wiped the tickle away, weighted every corner, and restarted the treasure walk",
        "dialogue": '"A captain needs a crew," the helper said. "And sometimes four shells."',
        "resolution": "The map stayed open long enough to lead everyone to a heart-shaped stone.",
        "ending": "At sunset, the weighted map lay flat beside the heart-shaped stone while the feather sailed harmlessly out to sea.",
        "object": "treasure map",
    },
    {
        "goal": "win a shell-listening contest by hearing the quietest ocean hum",
        "premise": "had lined up three spiral shells for a serious listening contest",
        "problem": "a grain of windblown sand slipped into one nostril just as the judging began",
        "failed_action": "pressed a shell to one ear and attempted to swallow the sneeze",
        "consequence": "The trapped sneeze escaped as a squeak, and a nearby crab raised both claws as if awarding points.",
        "clue": "turning away from the wind stopped new sand from reaching the shells",
        "helper_action": "offered a tissue and moved the contest behind a driftwood log",
        "plan": "clean the sandy nostril, shelter the shells, and listen again",
        "child_action": "cleaned the sandy nostril, sheltered the shells, and listened again",
        "dialogue": '"The crab liked round one," the helper whispered. "Let us make round two quieter."',
        "resolution": "In the shelter, everyone heard a soft ocean hush inside the smallest shell.",
        "ending": "The little shell became the trophy, and the crab left one neat track beside it before the tide came in.",
        "object": "smallest shell",
    },
    {
        "goal": "launch a bright kite in one smooth, impressive swoop",
        "premise": "had practiced a grand kite launch all week",
        "problem": "a dry wisp of sea grass brushed one nostril while the kite tugged",
        "failed_action": "jerked the spool away from the tickle instead of watching the string",
        "consequence": "The kite looped around a signpost and wore its tail like a droopy mustache.",
        "clue": "the kite went slack whenever the spool was lowered toward the sand",
        "helper_action": "held out a tissue and steadied the spool at knee height",
        "plan": "wipe the nostril, lower the spool, unwind the loop, and relaunch in a gentler breeze",
        "child_action": "wiped the nostril, lowered the spool, unwound the loop, and relaunched into a gentler breeze",
        "dialogue": '"First your nose, then the knots," the helper said. "The sky can wait one minute."',
        "resolution": "The second launch rose straight above the coast, with no signpost wearing a mustache.",
        "ending": "The kite floated over the water like a bright stamp on the evening sky, and its tail pointed safely home.",
        "object": "bright kite",
    },
    {
        "goal": "finish a sandcastle moat before the next thin wave arrived",
        "premise": "was building a sandcastle with a moat shaped like a wiggly smile",
        "problem": "a bubble of salty foam popped beneath one nostril",
        "failed_action": "kept digging while squinting upward and trying not to sniff",
        "consequence": "A sudden sneeze flattened one tower and launched its shell flag into the moat.",
        "clue": "water was escaping through a narrow crack beside the fallen tower",
        "helper_action": "passed over a tissue and cupped damp sand around the leaking crack",
        "plan": "clean the salty nostril, pack the crack, and rebuild the tower with a wider base",
        "child_action": "cleaned the salty nostril, packed the crack, and rebuilt the tower with a wider base",
        "dialogue": '"That sneeze found the weak spot," the helper said. "Very dramatic engineering."',
        "resolution": "The repaired moat filled evenly and carried the shell flag in one proud circle.",
        "ending": "When the next wave arrived, the broad tower remained standing with a silver moat shining around it.",
        "object": "sandcastle moat",
    },
    {
        "goal": "tell the perfect picnic joke before anyone took the last strawberry",
        "premise": "had saved a brand-new joke for a picnic beside the sea",
        "problem": "the peppery smell of a snack crumb prickled one nostril",
        "failed_action": "rushed toward the punch line while holding the sneeze behind puffed cheeks",
        "consequence": "The sneeze shouted the final word, and a gull used the surprise to steal an empty napkin.",
        "clue": "the crumb on the upper lip was causing the peppery tickle",
        "helper_action": "offered a tissue and covered the picnic bowl before the gull circled back",
        "plan": "wipe away the crumb, take one calm breath, and retell the joke from the beginning",
        "child_action": "wiped away the crumb, took one calm breath, and retold the joke from the beginning",
        "dialogue": '"Your nose told its own joke first," the helper said, laughing.',
        "resolution": "The second punch line landed clearly, and even the people at the next blanket laughed.",
        "ending": "The last strawberry was split in two as the gull strutted away with its useless napkin cape.",
        "object": "picnic joke",
    },
    {
        "goal": "sketch a tide-pool anemone before it folded beneath the water",
        "premise": "had opened a sketchbook beside a tide pool full of tiny moving colors",
        "problem": "cold salt mist settled inside one nostril",
        "failed_action": "leaned closer to the page and tried to finish one delicate line before sneezing",
        "consequence": "The sneeze dotted the paper with water and made the anemone look as though it wore spectacles.",
        "clue": "the page stayed dry beneath the overhang of a flat rock",
        "helper_action": "gave over a tissue and clipped the damp page beneath the flat rock",
        "plan": "clear the nostril, move into the rock's shelter, and turn the water dots into bubbles",
        "child_action": "cleared the nostril, moved into the rock's shelter, and turned the water dots into bubbles",
        "dialogue": '"Those spectacles are surprisingly stylish," the helper said.',
        "resolution": "The anemone opened again, and the finished sketch showed both its waving arms and a trail of bubbles.",
        "ending": "On the walk home, the dry sketchbook page fluttered open to an anemone wearing two perfect bubble spectacles.",
        "object": "tide-pool sketch",
    },
    {
        "goal": "balance seven smooth pebbles higher than a toy bucket",
        "premise": "had arranged a pebble-balancing show on a patch of firm sand",
        "problem": "powdery shell dust blew against one nostril",
        "failed_action": "reached for the seventh pebble with one eye closed against the tickle",
        "consequence": "The stack clicked down like stone dominoes, uncovering a tiny crab beneath the bottom pebble.",
        "clue": "the crab needed a clear path back toward the wet sand",
        "helper_action": "held out a tissue and drew a safe path around the scattered pebbles",
        "plan": "clean the nostril, guide the crab through, and rebuild away from its path",
        "child_action": "cleaned the nostril, guided the crab through, and rebuilt a shorter stack away from its path",
        "dialogue": '"Our smallest audience member was underneath the stage," the helper said.',
        "resolution": "The new five-pebble tower stood steady, and the crab reached a ribbon of shallow water.",
        "ending": "Five stones made a sunset shadow on the sand while the crab's tracks stitched a line toward the shining tide.",
        "object": "pebble tower",
    },
    {
        "goal": "imitate the harbor horn loudly enough for a cousin to hear",
        "premise": "had been practicing a deep harbor-horn sound along the rail",
        "problem": "a bead of spray cooled one nostril in the middle of a mighty breath",
        "failed_action": "forced the horn sound out before the tickle could win",
        "consequence": "The sound came out half honk and half sneeze, and three seals turned toward shore at once.",
        "clue": "the seals answered the strange little honk instead of swimming away",
        "helper_action": "offered a tissue and counted a slower breathing rhythm",
        "plan": "wipe the nostril, breathe gently, and answer the seals with one softer honk",
        "child_action": "wiped the nostril, breathed gently, and answered the seals with one softer honk",
        "dialogue": '"Congratulations," the helper said. "You speak accidental seal."',
        "resolution": "One seal barked back, and the whole family bowed as if the duet had been planned.",
        "ending": "Beyond the rail, three round seal heads bobbed in the copper water while one soft honk drifted after them.",
        "object": "harbor-horn duet",
    },
    {
        "goal": "take one dignified family photograph beside the waves",
        "premise": "had chosen the most serious pose possible for a family photograph",
        "problem": "the coconut smell of sunscreen made one nostril quiver",
        "failed_action": "froze in the serious pose and attempted to smile without breathing",
        "consequence": "The sneeze arrived exactly as the camera clicked, producing a photograph of flying hair and astonished eyebrows.",
        "clue": "everyone laughed harder at the surprise picture than at any careful pose",
        "helper_action": "passed over a tissue and showed the funny photograph on the camera",
        "plan": "wipe the nostril and invite everyone to make a silly face for one more picture",
        "child_action": "wiped the nostril and asked everyone to make their silliest face for one more picture",
        "dialogue": '"Dignity can have the next photograph," the helper said.',
        "resolution": "The second picture caught seven silly faces and one calm, sneeze-free nose.",
        "ending": "That night, the surprise photograph stood on the table beside the silly one, and both made the family laugh again.",
        "object": "family photograph",
    },
    {
        "goal": "conduct a shell orchestra for people resting on the boardwalk",
        "premise": "had sorted shells into clackers, scrapers, and one grand conch drum",
        "problem": "a thread of dried seaweed curled against one nostril",
        "failed_action": "waved the conducting stick faster, hoping the music would hide every sniff",
        "consequence": "A sneeze struck the conch with the stick and added an enormous BONK in the quietest part.",
        "clue": "the musicians copied the BONK and turned it into a steady beat",
        "helper_action": "removed the seaweed with a tissue and tapped the new rhythm on an upside-down pail",
        "plan": "clear the nostril, count the beat, and conduct the accidental rhythm on purpose",
        "child_action": "cleared the nostril, counted the beat, and conducted the accidental rhythm on purpose",
        "dialogue": '"Every orchestra needs one surprise instrument," the helper said.',
        "resolution": "The clackers, scrapers, pail, and conch finished together on one cheerful BONK.",
        "ending": "As the sky turned pink, the shells rested in a neat row and the pail held the final beat like a small round echo.",
        "object": "shell orchestra",
    },
]


THINKING_MODES = [
    {
        "role": "a detective",
        "opening": "I shall inspect every clue and remain extremely dignified.",
        "mistake": "Clue one: my nostril is plotting. Bad deduction: pretend it is not.",
        "turn": "New evidence: {clue}. That means I should {plan}.",
        "victory": "Case closed. The culprit was tiny, but its comedy was enormous.",
    },
    {
        "role": "a stage director",
        "opening": "Places, everyone. My nose has no speaking part in this scene.",
        "mistake": "Why is my nostril improvising? This is not in the script.",
        "turn": "Pause the show because {clue}. The next scene is to {plan}.",
        "victory": "Curtain call for calm breathing and a much better ending.",
    },
    {
        "role": "a scientist",
        "opening": "Today I will test whether looking impressive is scientifically possible.",
        "mistake": "Observation: the nostril wiggles. Hypothesis: ignoring it will definitely work. Probably.",
        "turn": "Revised hypothesis: because {clue}, I need to {plan}.",
        "victory": "Experiment complete. Tissues remain a powerful coastal technology.",
    },
    {
        "role": "a sports announcer",
        "opening": "Welcome to the coast, where I am favored to win against the wind.",
        "mistake": "The nostril enters the contest! The crowd did not request this player.",
        "turn": "A clever timeout reveals that {clue}. The comeback move is to {plan}.",
        "victory": "And that is the whistle! Team Sensible Choice wins the day.",
    },
    {
        "role": "a ship captain",
        "opening": "Steady course. No tiny nose trouble shall rock this expedition.",
        "mistake": "Nostril squall ahead! I may have underestimated the weather.",
        "turn": "Change course: {clue}. All hands, prepare to {plan}.",
        "victory": "The ship is safe, the nose is calm, and the captain has learned to accept help.",
    },
    {
        "role": "a mechanic",
        "opening": "Everything is running smoothly, including, I hope, my breathing parts.",
        "mistake": "Rattle in the nostril department. Pretending not to hear it has failed inspection.",
        "turn": "There is the cause: {clue}. The proper repair is to {plan}.",
        "victory": "Repair complete. No spare nose parts were required.",
    },
    {
        "role": "an explorer",
        "opening": "I am entering unexplored coastal territory with courage and excellent hair.",
        "mistake": "A wild nostril tickle! The guidebook said nothing about this.",
        "turn": "The trail becomes clear: {clue}. I can move forward if I {plan}.",
        "victory": "Discovery: asking for help does not make an adventure smaller.",
    },
    {
        "role": "a magician",
        "opening": "Behold! I shall perform the famous trick called Looking Completely Cool.",
        "mistake": "My nostril has produced the wrong surprise. Where is the trapdoor for sneezes?",
        "turn": "The secret is ordinary, not magical: {clue}. Now I will {plan}.",
        "victory": "Ta-da! The greatest trick was fixing the real problem.",
    },
    {
        "role": "a calm coach",
        "opening": "First goal: enjoy the coast. Second goal: do not panic about small things.",
        "mistake": "I am holding my breath, which Coach Me would call a very questionable play.",
        "turn": "Slow down and notice: {clue}. The useful next step is to {plan}.",
        "victory": "Good recovery. Laugh, learn, and keep going.",
    },
    {
        "role": "a comedian",
        "opening": "The coast has waves, gulls, and now one extremely professional entertainer: me.",
        "mistake": "Apparently my nostril has brought its own joke and refuses to wait its turn.",
        "turn": "Here is the twist: {clue}. I can improve the ending if I {plan}.",
        "victory": "A small disaster plus a sensible choice equals a story worth retelling.",
    },
]


@dataclass
class StoryParams:
    name: str = "Milo"
    helper: str = "mom"
    coast_feature: str = "pier"
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ["sand", "salt", "tissue", "distance"]:
            self.meters.setdefault(k, 0.0)
        for k in ["embarrassment", "worry", "relief", "confidence", "amusement"]:
            self.memes.setdefault(k, 0.0)


@dataclass
class World:
    place: str = "the coast"
    feature: str = "pier"
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy

        w = World(place=self.place, feature=self.feature)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        return w


def inner_thought(world: World, name: str, text: str) -> None:
    world.say(f'{name} thought, "{text}"')


def _seed_number(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    stable = f"{params.name}|{params.helper}|{params.coast_feature}"
    return int.from_bytes(stable.encode("utf-8"), "little")


def _helper_subject(label: str) -> str:
    return label[0].upper() + label[1:] if label else "A helper"


def _helper_attribution(label: str) -> str:
    return label.capitalize() if label in {"mom", "dad"} else label


def tell_world(params: StoryParams) -> World:
    seed = _seed_number(params)
    rng = random.Random(seed)
    incident_index = seed % len(INCIDENTS)
    thinking_index = (seed // len(INCIDENTS)) % len(THINKING_MODES)
    incident = INCIDENTS[incident_index]
    thinking = THINKING_MODES[thinking_index]
    w = World(feature=params.coast_feature)
    child = w.add(Entity(
        id=params.name,
        kind="character",
        label=params.name,
        traits=["little", rng.choice(ADJ_POOL)],
    ))
    helper = w.add(Entity(id="helper", kind="character", label=params.helper))
    tissue = w.add(Entity(id="tissue", label="a crumpled tissue"))
    focus = w.add(Entity(id="focus", label=incident["object"]))
    w.facts.update(
        child=child,
        helper=helper,
        tissue=tissue,
        focus=focus,
        params=params,
        incident=incident,
        thinking=thinking,
        incident_index=incident_index,
        thinking_index=thinking_index,
    )

    # The chosen goal establishes the premise before the comic interruption.
    w.say(
        f"At the coast near the {w.feature}, {child.id} {incident['premise']}."
    )
    w.say(
        f"The plan was to {incident['goal']} while the wind, gulls, and waves supplied a noisy audience."
    )
    inner_thought(w, child.id, thinking["opening"])
    w.para()

    # The failed attempt makes the physical tickle cause a visible consequence.
    child.memes["worry"] += 1
    child.memes["embarrassment"] += 1
    child.meters["salt"] += 1
    if "sand" in incident["problem"] or "dust" in incident["problem"]:
        child.meters["sand"] += 1
    child.meters["distance"] = 6
    w.say(f"Then {incident['problem']}.")
    inner_thought(w, child.id, thinking["mistake"])
    w.say(f"Trying to look unbothered, {child.id} {incident['failed_action']}.")
    w.say(incident["consequence"])
    w.facts["problem"] = incident["problem"]
    w.facts["consequence"] = incident["consequence"]
    w.para()

    # The inner monologue interprets a grounded clue and changes the next action.
    helper_name = _helper_subject(params.helper)
    w.say(f"{helper_name} noticed what had happened. {helper_name} {incident['helper_action']}.")
    w.say(incident["dialogue"].replace("the helper", _helper_attribution(params.helper)))
    inner_thought(
        w,
        child.id,
        thinking["turn"].format(clue=incident["clue"], plan=incident["plan"]),
    )
    w.say(f"So {child.id} {incident['child_action']}.")

    child.memes["amusement"] += 1
    child.memes["relief"] += 1
    child.meters["tissue"] += 1
    child.memes["confidence"] += 1
    child.memes["worry"] = 0
    child.memes["embarrassment"] = 0
    child.meters["distance"] = 1
    w.say(incident["resolution"])
    inner_thought(w, child.id, thinking["victory"])
    w.para()
    w.say(incident["ending"])
    w.facts["resolved"] = True
    w.facts["inner_monologue"] = True
    w.facts["clue"] = incident["clue"]
    w.facts["solution"] = incident["child_action"]
    w.facts["ending"] = incident["ending"]
    return w


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    incident = world.facts["incident"]
    thinking = world.facts["thinking"]
    return [
        f"Write a funny story about {p.name} at the coast trying to {incident['goal']} when a nostril problem interrupts.",
        f"Tell a coast comedy with a strong inner monologue in which {p.name} thinks like {thinking['role']} and accepts help from {p.helper}.",
        f"Create a child-friendly story near the {p.coast_feature} about a silly nostril problem, a useful clue, a tissue, and a concrete ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    incident = world.facts["incident"]
    thinking = world.facts["thinking"]
    return [
        QAItem(
            question=f"What does {p.name} hope to do near the {p.coast_feature}?",
            answer=f"{p.name} hopes to {incident['goal']} at the coast.",
        ),
        QAItem(
            question=f"What nostril problem interrupts {p.name}, and what goes wrong next?",
            answer=f"{incident['problem'].capitalize()}. {incident['consequence']}",
        ),
        QAItem(
            question=f"What clue guides {p.name}'s inner monologue as {thinking['role']}?",
            answer=f"{p.name} notices that {incident['clue']}. That clue leads to a practical new plan.",
        ),
        QAItem(
            question=f"How do {p.name} and {p.helper} solve the comic problem?",
            answer=f"{_helper_subject(p.helper)} {incident['helper_action']}. Then {p.name} {incident['child_action']}, so {incident['resolution'][0].lower() + incident['resolution'][1:]}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is sea spray?",
            answer="Sea spray is tiny drops of salty water blown off the ocean by the wind.",
        ),
        QAItem(
            question="What is a tissue used for?",
            answer="A tissue is a soft piece of paper used for wiping a nose or cleaning little messes.",
        ),
        QAItem(
            question="Why can wind feel cold at the coast?",
            answer="Wind can feel cold at the coast because it carries cooler air and salty moisture across your skin.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 3) for k, v in e.meters.items() if v}
        memes = {k: round(v, 3) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id} ({e.kind}) {' '.join(bits)}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
% A child is amused if the salty tickle gets solved with a tissue.
solved(Child) :- problem(Child, nostril_tickle), has_tissue(Child).
amused(Child) :- solved(Child).

% The coast joke is valid only when the problem is about wind, salt, and a nostril.
valid_story(Place, Feature) :- place(Place), feature(Feature), coast(Place), feature_of(Place, Feature).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("coast", "the_coast"),
        asp.fact("place", "the_coast"),
        asp.fact("feature", "pier"),
        asp.fact("feature", "dunes"),
        asp.fact("feature", "boardwalk"),
        asp.fact("feature", "rocky_shore"),
        asp.fact("feature", "shell_path"),
    ]
    for f in COAST_FEATURES:
        lines.append(asp.fact("feature_of", "the_coast", f.replace(" ", "_")))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as err:
        print(f"ASP unavailable: {err}")
        return 1
    model = asp.one_model(asp_program("#show valid_story/2."))
    atoms = set(asp.atoms(model, "valid_story"))
    expected = {("the_coast", f.replace(" ", "_")) for f in COAST_FEATURES}
    if atoms == expected:
        print(f"OK: ASP parity matches ({len(atoms)} valid story features).")
        return 0
    print("MISMATCH between ASP and Python facts:")
    print("  ASP:", sorted(atoms))
    print("  PY :", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comedic coast storyworld with inner monologue.")
    ap.add_argument("--name", choices=NAME_POOL)
    ap.add_argument("--helper", choices=HELPER_POOL)
    ap.add_argument("--coast-feature", choices=COAST_FEATURES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        name=args.name or rng.choice(NAME_POOL),
        helper=args.helper or rng.choice(HELPER_POOL),
        coast_feature=args.coast_feature or rng.choice(COAST_FEATURES),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        print(sorted(asp.atoms(model, "valid_story")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for i, feature in enumerate(COAST_FEATURES):
            p = StoryParams(
                name=NAME_POOL[i % len(NAME_POOL)],
                helper=HELPER_POOL[i % len(HELPER_POOL)],
                coast_feature=feature,
                seed=base_seed + i,
            )
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
