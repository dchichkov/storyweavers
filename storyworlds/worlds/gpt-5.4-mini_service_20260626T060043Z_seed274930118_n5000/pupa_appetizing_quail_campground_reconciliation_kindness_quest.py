#!/usr/bin/env python3
"""
pupa_appetizing_quail_campground_reconciliation_kindness_quest.py
=================================================================

A small Animal-Story-style world about a campground quest where a pupa,
an appetizing snack, and a quail become part of a reconciliation story.

Premise:
- A young animal wants to take part in a campground quest.
- A tempting appetizing treat creates tension.
- A quail's nest or a shared snack gets tangled in the choice.
- Kindness and reconciliation turn the moment into a gentle ending.

The story is state-driven: characters have physical meters and emotional memes,
the world tracks simple causal facts, and the ending image proves what changed.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402

# ---------------------------------------------------------------------------
# World data
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the campground"
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    name: str
    verb: str
    gerund: str
    rush: str
    risk: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Treat:
    id: str
    label: str
    phrase: str
    tempt: str
    region: str
    mess: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "campground": Setting(place="the campground", affords={"quest"}),
}

QUESTS = {
    "quest": Quest(
        id="quest",
        name="reconciliation quest",
        verb="follow the trail",
        gerund="following the trail",
        rush="dash toward the pine path",
        risk="leave a friend behind",
        keyword="quest",
        tags={"quest", "reconciliation", "kindness"},
    ),
}

TASTES = {
    "snack": Treat(
        id="snack",
        label="appetizing snack",
        phrase="an appetizing snack wrapped in paper",
        tempt="look delicious",
        region="snout",
        mess="crumbs",
    ),
}

GIRL_NAMES = ["Mina", "Luna", "Pippa", "Nora", "Tia"]
BOY_NAMES = ["Bram", "Otto", "Milo", "Finn", "Rowan"]
ANIMAL_TYPES = ["rabbit", "fox", "badger", "squirrel", "deer"]
TRAITS = ["curious", "gentle", "brave", "quiet", "kind"]

SCENARIOS = [
    {
        "id": "nest_marker",
        "premise": "A quail had tucked her nest beside the first quest marker.",
        "conflict": "A strip of appetizing berry bread lay beyond it, and the shortest reach would have crushed the sheltering grass.",
        "mistake": "leaned over the nest before noticing an egg wobble",
        "clue": "the mother quail's sharp warning call",
        "repair": "backed away, marked a wide path with pinecones, and divided the bread with {helper}",
        "lesson": "a prize is never worth frightening a family",
        "ending": "the quail settled over her eggs while two neat trails of pinecones curved toward the sunset",
    },
    {
        "id": "missing_map",
        "premise": "The quest map vanished just as a quail darted beneath the picnic table.",
        "conflict": "{hero} accused {helper} of moving it after finding appetizing crumbs on the empty map board.",
        "mistake": "spoke before searching carefully",
        "clue": "a corner of paper caught beneath the pupa's wind screen",
        "repair": "apologized, freed the map without touching the pupa, and asked {helper} to read the next clue aloud",
        "lesson": "questions mend more than quick blame",
        "ending": "the flattened map glowed beside the lantern, with one shared crumb resting on each plate",
    },
    {
        "id": "fallen_pupa",
        "premise": "Wind knocked the pupa's twig shelter into the quest trail.",
        "conflict": "The rescue whistle was across the campground beside an appetizing apple tart, and {hero} wanted to race for both.",
        "mistake": "ran ahead without explaining the plan",
        "clue": "the quail pacing around the exposed pupa instead of fleeing",
        "repair": "returned to {helper}, carried the twig together, and rebuilt the shelter before sharing the tart",
        "lesson": "kindness begins by making sure nobody is left exposed",
        "ending": "under a roof of crossed twigs, the pupa rested as the quail's footprints circled the fresh earth",
    },
    {
        "id": "quail_canteen",
        "premise": "A thirsty quail pecked at the quest team's nearly empty canteen.",
        "conflict": "The next station offered appetizing melon only to teams that arrived with water to spare.",
        "mistake": "pulled the cup away and made the quail stumble",
        "clue": "a dry pupa case and curled leaves beside the dusty bird",
        "repair": "said sorry, poured a shallow drink, and worked with {helper} to collect dew in broad leaves",
        "lesson": "sharing a little can reveal a better solution",
        "ending": "three dew-filled leaves shone by the trail while the refreshed quail chirped from a stump",
    },
    {
        "id": "snack_bag",
        "premise": "The campground's quest prize was an appetizing bag of seed cakes.",
        "conflict": "A quail tugged the loose string, scattering cakes dangerously close to the pupa's log.",
        "mistake": "shouted at the bird and snatched the bag",
        "clue": "plastic thread looped around the quail's ankle",
        "repair": "held still while {helper} cut the thread, then gathered every wrapper and offered safe seeds away from the pupa",
        "lesson": "understanding the trouble comes before judging who caused it",
        "ending": "the clean grass held no string at all, only a row of quail tracks beside the protected log",
    },
    {
        "id": "bridge_riddle",
        "premise": "The reconciliation quest stopped at a muddy miniature bridge.",
        "conflict": "{hero} and {helper} argued over whose bridge design could carry an appetizing picnic basket without disturbing a quail nearby.",
        "mistake": "pushed one plank into place and splashed mud on {helper}",
        "clue": "the pupa's silk threads crossing in a strong, gentle lattice",
        "repair": "wiped away the splash, combined both designs, and invited {helper} to tie the final crossing",
        "lesson": "two careful ideas can support more than one stubborn idea",
        "ending": "the basket crossed on a woven bridge as the quail stepped safely through the reeds below",
    },
    {
        "id": "bell_echo",
        "premise": "Quest bells were hidden around the campground, each tuned to a different note.",
        "conflict": "An appetizing cinnamon smell distracted {hero}, who rang the loudest bell beside a sleeping pupa and startled a quail.",
        "mistake": "laughed at the noise when {helper} asked for quiet",
        "clue": "the pupa's twig trembling long after the echo faded",
        "repair": "apologized, wrapped the bell in a scarf, and followed {helper}'s silent hand signals to the next station",
        "lesson": "fun becomes kinder when everyone can feel safe",
        "ending": "at dusk, one muffled chime floated over the fire while the quail slept with her head beneath a wing",
    },
    {
        "id": "berry_stain",
        "premise": "A purple stain appeared across the campground quest flag.",
        "conflict": "{helper} thought {hero}'s appetizing berry pocket had leaked, and {hero} angrily blamed a passing quail.",
        "mistake": "hid the sticky pocket instead of telling the truth",
        "clue": "a berry-colored pawprint beside the pupa viewing jar",
        "repair": "admitted the spill, washed the flag with {helper}, and moved the clean viewing jar into shade",
        "lesson": "honesty gives reconciliation somewhere firm to begin",
        "ending": "the clean flag fluttered above two purple-stained paws and a quail pecking harmless berries below",
    },
    {
        "id": "lost_chick",
        "premise": "A young quail became separated from its family during the campground quest.",
        "conflict": "The last appetizing oat biscuit was also the team's final trail token, and its smell was the only thing that made the chick follow.",
        "mistake": "refused to risk the token until {helper} turned away in disappointment",
        "clue": "tiny tracks circling the pupa log and leading toward a worried call",
        "repair": "crumbled the biscuit into a safe trail and asked {helper} to guard the chick from hikers",
        "lesson": "finishing first matters less than helping someone get home",
        "ending": "beneath the finish banner, the reunited quail family shared crumbs while the unused prize ribbon stirred overhead",
    },
    {
        "id": "lantern_heat",
        "premise": "Cold fog covered the campground before the evening quest.",
        "conflict": "{hero} moved a lantern close to warm an appetizing pot of soup, not seeing the pupa attached to the lantern post.",
        "mistake": "dismissed {helper}'s warning as needless worry",
        "clue": "a quail spreading her wings between the heat and the pupa",
        "repair": "moved the lantern to a stone ring, thanked {helper}, and warmed the soup with reflected heat instead",
        "lesson": "listening can protect a life too small to speak",
        "ending": "steam curled from the soup across the fire ring while the pupa hung cool beneath a silver drop of fog",
    },
    {
        "id": "painted_stones",
        "premise": "Painted stones were supposed to guide every team through the kindness quest.",
        "conflict": "{hero} secretly turned one arrow toward an appetizing pancake station, sending {helper} near a quail's nesting hollow.",
        "mistake": "changed a shared sign for a private reward",
        "clue": "the same blue paint on {hero}'s paw and the backward arrow",
        "repair": "confessed, restored the marker, and walked behind {helper} while they checked every remaining sign",
        "lesson": "trust returns through truthful actions, not clever excuses",
        "ending": "all the blue arrows pointed home, and the quail watched from beside a pupa-shaped shadow on the final stone",
    },
    {
        "id": "rain_shelter",
        "premise": "Rain began while the quest teams carried an appetizing picnic through the campground.",
        "conflict": "Only one dry shelter remained, but a soaked quail and a pupa-covered branch already occupied its corner.",
        "mistake": "dragged the basket inside without leaving room for {helper}",
        "clue": "rain running from {helper}'s ears while the quail tucked closer around the pupa",
        "repair": "came back out, used the picnic cloth as a wider roof, and held one side while {helper} secured the other",
        "lesson": "comfort feels best when it is made wide enough to share",
        "ending": "raindrops drummed above a dry circle of friends, one quiet pupa, and a quail preening her feathers",
    },
]

OPENINGS = [
    "At first light, {hero}, a {trait} {species}, studied the quest board at the campground.",
    "The campground smelled of wet bark when {hero}, the {trait} {species}, reported for a reconciliation quest.",
    "Before the breakfast bell, {hero} the {species} promised to complete the campground's kindness quest.",
    "A trail ribbon snapped in the breeze as {hero}, a {trait} {species}, joined {helper} at the campground.",
    "On the busiest campground morning of summer, {hero} the {species} volunteered for a quest about kindness.",
    "Under tall pines, {hero}, the campground's {trait} {species}, opened the first quest envelope.",
    "The ranger's map called it a reconciliation quest, and {hero} the {species} wanted to prove ready for it.",
    "Campfire smoke curled above the campground as {hero}, a {trait} {species}, chose the kindness trail.",
]

DIALOGUE = [
    '"Let me explain what I saw," {helper} said. "Then we can fix it together."',
    '"Being sorry is a start," said {helper}. "Show me what you will do next."',
    '"Wait," {helper} said gently. "The smallest clue may be the important one."',
    '"I was hurt, but I am listening," {helper} replied. "Tell me the truth."',
    '"A quest is not a race away from our mistakes," {helper} said.',
    '"We can disagree and still work side by side," {helper} reminded {hero}.',
    '"Kindness needs hands as well as words," said {helper}.',
    '"Look once more before deciding," {helper} whispered.',
]


# ---------------------------------------------------------------------------
# Reasonableness gate and ASP twin
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for quest_id in setting.affords:
            for treat_id in TASTES:
                combos.append((place, quest_id, treat_id))
    return combos


ASP_RULES = r"""
place(campground).
affords(campground,quest).
quest(quest).
treat(snack).
valid(Place,Quest,Treat) :- place(Place), affords(Place,Quest), treat(Treat), quest(Quest).
#show valid/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for place, setting in SETTINGS.items():
        for q in sorted(setting.affords):
            lines.append(asp.fact("affords", place, q))
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
    for t in TASTES:
        lines.append(asp.fact("treat", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story model
# ---------------------------------------------------------------------------

def predict(world: World, hero: Entity, quest: Quest, treat: Treat) -> dict:
    sim = world.copy()
    _begin_quest(sim, sim.get(hero.id), quest, narrate=False)
    _tempt(sim, sim.get(hero.id), treat, narrate=False)
    return {
        "mess": sim.get(hero.id).meters.get("crumbs", 0) >= THRESHOLD,
        "hurt_feelings": sim.get(hero.id).memes.get("hurt", 0) >= THRESHOLD,
    }


def _begin_quest(world: World, hero: Entity, quest: Quest, narrate: bool = True) -> None:
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    world.facts["quest_started"] = True
    if narrate:
        world.say(
            f"{hero.id} wanted to join the {quest.name} at {world.setting.place}, "
            f"because the trail looked exciting."
        )


def _tempt(world: World, hero: Entity, treat: Treat, narrate: bool = True) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0) + 1
    if narrate:
        world.say(
            f"Near the fire ring, an {treat.label} began to {treat.tempt}, "
            f"and {hero.id} paused to sniff the air."
        )


def _messy_choice(world: World, hero: Entity, treat: Treat, narrate: bool = True) -> None:
    hero.meters[treat.mess] = hero.meters.get(treat.mess, 0) + 1
    hero.memes["guilt"] = hero.memes.get("guilt", 0) + 1
    if narrate:
        world.say(
            f"{hero.id} took a bite too fast, and {treat.label} left {treat.mess} "
            f"on {hero.pronoun('possessive')} paws."
        )


def _apology(world: World, hero: Entity, helper: Entity, treat: Treat, narrate: bool = True) -> None:
    hero.memes["apology"] = hero.memes.get("apology", 0) + 1
    helper.memes["softness"] = helper.memes.get("softness", 0) + 1
    if narrate:
        world.say(
            f"{hero.id} lowered {hero.pronoun('possessive')} head and said sorry to "
            f"{helper.id}, then offered to wipe the crumbs away."
        )


def _reconcile(world: World, hero: Entity, helper: Entity, quest: Quest, treat: Treat, narrate: bool = True) -> None:
    hero.memes["kindness"] = hero.memes.get("kindness", 0) + 1
    hero.memes["peace"] = 1
    helper.memes["peace"] = 1
    if narrate:
        world.say(
            f"{helper.id} smiled and shared the {treat.label} more slowly, and "
            f"{hero.id} promised to be careful on the {quest.gerund} path."
        )
        world.say(
            f"Together they walked on, side by side, with the trail ahead and "
            f"their friendship feeling lighter."
        )


def run_world(world: World, hero: Entity, helper: Entity, quest: Quest, treat: Treat) -> None:
    _begin_quest(world, hero, quest)
    world.para()
    _tempt(world, hero, treat)
    if predict(world, hero, quest, treat)["mess"]:
        _messy_choice(world, hero, treat)
        world.say(
            f"{helper.id} noticed the mess and did not scold {hero.id}; instead, "
            f"{helper.id} gave a calm look and a cloth."
        )
        _apology(world, hero, helper, treat)
        _reconcile(world, hero, helper, quest, treat)
    else:
        world.say(
            f"Nothing went wrong, so {hero.id} and {helper.id} kept walking "
            f"through the campground with easy smiles."
        )


# ---------------------------------------------------------------------------
# Parameters and generation
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    quest: str
    treat: str
    name: str
    species: str
    helper: str
    trait: str
    seed: Optional[int] = None
    scenario: str = "nest_marker"
    telling: int = 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal Story world: a campground quest with kindness and reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--treat", choices=TASTES)
    ap.add_argument("--name")
    ap.add_argument("--species", choices=ANIMAL_TYPES)
    ap.add_argument("--helper", choices=["friend", "parent", "ranger"])
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.quest is None or c[1] == args.quest)
        and (args.treat is None or c[2] == args.treat)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, quest, treat = rng.choice(sorted(combos))
    species = args.species or rng.choice(ANIMAL_TYPES)
    name = args.name or rng.choice(GIRL_NAMES if rng.random() < 0.5 else BOY_NAMES)
    helper = args.helper or rng.choice(["friend", "parent", "ranger"])
    trait = args.trait or rng.choice(TRAITS)
    scenario = rng.choice(SCENARIOS)["id"]
    telling = rng.randrange(1_000_000)
    return StoryParams(
        place=place,
        quest=quest,
        treat=treat,
        name=name,
        species=species,
        helper=helper,
        trait=trait,
        scenario=scenario,
        telling=telling,
    )


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.species, memes={}, meters={}))
    helper = world.add(Entity(id=params.helper.capitalize(), kind="character", type="adult", label=params.helper))
    world.add(Entity(id="pupa", type="pupa", label="pupa"))
    quest = QUESTS[params.quest]
    treat = TASTES[params.treat]
    scenario = next(s for s in SCENARIOS if s["id"] == params.scenario)
    rng = random.Random(params.telling)
    values = {"hero": hero.id, "helper": helper.id, "trait": params.trait, "species": params.species}
    opening = rng.choice(OPENINGS).format(**values)
    dialogue = rng.choice(DIALOGUE).format(**values)
    admission = rng.choice([
        f'"I chose too quickly," {hero.id} admitted.',
        f'"I cared more about winning than listening," {hero.id} said.',
        f'"That was my mistake, and I am sorry," {hero.id} told {helper.id}.',
        f'{hero.id} took a breath. "I hurt you. May I help repair it?"',
        f'"I cannot undo it," {hero.id} said, "but I can make the next choice kinder."',
        f'{hero.id} faced {helper.id}. "You deserved the truth sooner."',
    ])
    turn = rng.choice([
        "That clue changed the shape of the whole problem.",
        f"For the first time, {hero.id} stopped thinking about the finish ribbon.",
        "The quest suddenly seemed less about winning and more about noticing.",
        f"Seeing it clearly made {hero.id}'s cheeks grow warm with regret.",
        "Instead of defending the mistake, the young adventurer looked for its cause.",
        f"{helper.id} waited, giving the truth enough quiet to be heard.",
    ])
    reconciliation = rng.choice([
        f"{helper.id} accepted the apology after watching the careful repair.",
        f"The tight feeling between them eased when {hero.id} finished the repair.",
        f"They did not pretend the mistake had vanished, but they trusted each other again.",
        f"By working together, {hero.id} and {helper.id} made peace instead of merely saying it.",
        f"Their reconciliation grew from the apology and the action that followed it.",
        f"{helper.id} smiled at last, and the two rejoined the quest side by side.",
    ])
    pupa_link = rng.choice([
        "Nearby, the pupa remained still, a quiet reminder that important changes can happen out of sight.",
        "They checked the pupa before moving on and left its shelter untouched.",
        "Even the silent pupa belonged in the circle of care they made.",
        "Beside them, the pupa waited safely for its own transformation.",
    ])

    world.say(opening)
    world.say(scenario["premise"].format(**values))
    world.para()
    world.say(scenario["conflict"].format(**values))
    world.say(f"In the rush, {hero.id} {scenario['mistake'].format(**values)}.")
    world.say(dialogue)
    world.para()
    world.say(f"Then they noticed {scenario['clue'].format(**values)}. {turn}")
    world.say(admission)
    world.say(f"To put things right, {hero.id} {scenario['repair'].format(**values)}.")
    world.para()
    world.say(reconciliation)
    world.say("This was reconciliation made real: kindness in words, followed by kindness in action.")
    world.say(f"{hero.id} understood that {scenario['lesson']}.")
    world.say(pupa_link)
    world.say(f"Their final campground image was this: {scenario['ending'].format(**values)}.")

    hero.memes.update({"guilt": 1, "apology": 1, "kindness": 1, "peace": 1})
    helper.memes.update({"hurt": 1, "softness": 1, "peace": 1})

    world.facts = {
        "hero": hero,
        "helper": helper,
        "quest": quest,
        "treat": treat,
        "params": params,
        "reconciled": hero.memes.get("peace", 0) >= THRESHOLD,
        "scenario": scenario,
        "mistake": scenario["mistake"].format(**values),
        "clue": scenario["clue"].format(**values),
        "repair": scenario["repair"].format(**values),
        "lesson": scenario["lesson"],
        "ending": scenario["ending"].format(**values),
    }

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest"]
    treat = f["treat"]
    return [
        f'Write a gentle animal story for young children set at a campground with a "reconciliation" turn.',
        f"Tell a story where {hero.id} wants to join a {quest.name} but an {treat.label} becomes tempting, and the friends resolve it kindly.",
        f'Write a simple campground tale that includes the words "pupa", "appetizing", and "quail" in a child-friendly way.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    return [
        QAItem(
            question=f"Where does {hero.id}'s story take place?",
            answer=f"It takes place at {world.setting.place}. That is where {hero.id} and {helper.id} undertake their kindness quest.",
        ),
        QAItem(
            question=f"What mistake did {hero.id} make?",
            answer=f"{hero.id} {f['mistake']}. The choice hurt trust and made the quest's real problem clear.",
        ),
        QAItem(
            question=f"What clue helped {hero.id} understand the problem?",
            answer=f"The important clue was {f['clue']}. It helped {hero.id} stop, reconsider, and listen.",
        ),
        QAItem(
            question=f"How did {hero.id} repair the harm?",
            answer=f"{hero.id} {f['repair']}. That concrete act of kindness allowed reconciliation with {helper.id}.",
        ),
        QAItem(
            question=f"What did {hero.id} learn from the quest?",
            answer=f"{hero.id} learned that {f['lesson']}. The final image is this: {f['ending']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pupa?",
            answer="A pupa is the resting stage of some insects while they change into their grown-up form.",
        ),
        QAItem(
            question="What does appetizing mean?",
            answer="Appetizing means something looks or smells tasty and makes you want to eat it.",
        ),
        QAItem(
            question="What is a quail?",
            answer="A quail is a small bird that lives on the ground and often moves in quick little steps.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means treating others gently, helping them, and choosing care instead of meanness.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation means making peace again after a disagreement or a hurt feeling.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey or task done to find something, learn something, or help someone.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts ==", *[f"- {p}" for p in sample.prompts], "", "== Story QA =="]
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{ent.id}: {ent.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="campground", quest="quest", treat="snack", name="Mina", species="rabbit", helper="friend", trait="kind"),
    StoryParams(place="campground", quest="quest", treat="snack", name="Bram", species="fox", helper="ranger", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
