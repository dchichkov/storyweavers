#!/usr/bin/env python3
"""
A standalone Storyweavers world: a tiny superhero story about breakfast trouble,
a sudden twist, and a reconciliation.

Premise:
- A young superhero team is getting ready for the morning.
- Bacon goes missing from the kitchen.
- A small twist changes who seems responsible.
- The misunderstanding is repaired with a calm reconciliation.

This script follows the Storyworld contract:
- standalone stdlib Python
- lazy ASP import for verification/query modes
- world simulation with physical meters and emotional memes
- StorySample/QAItem/StoryError from storyworlds.results
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
while ROOT != os.path.dirname(ROOT):
    if os.path.exists(os.path.join(ROOT, "storyworlds", "results.py")):
        break
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


SETTING = "sunrise city block"
SEED_WORDS = {"bacon", "remove"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    hidden_in: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ["missing", "steam", "crumbs", "scratched", "closed"]:
            self.meters.setdefault(k, 0.0)
        for k in ["worry", "hope", "trust", "anger", "bravery", "guilt", "relief", "teamwork"]:
            self.memes.setdefault(k, 0.0)


@dataclass
class StoryParams:
    hero: str = "Nova"
    partner: str = "Bolt"
    sidekick: str = "Penny"
    villain: str = "Dr. Crisp"
    twist: int = 0
    reconciliation_style: int = 0
    seed: Optional[int] = None


@dataclass(frozen=True)
class Case:
    mission: str
    trouble: str
    clue: str
    false_lead: str
    twist: str
    reveal: str
    misunderstanding: str
    reconciliation: str
    fix: str
    proof: str
    ending: str
    lesson: str


CASES = [
    Case(
        mission="protect the morning feast at headquarters",
        trouble="the bacon vanished from the kitchen tray just before breakfast bell",
        clue="a trail of grease dots leading toward the costume ladder",
        false_lead="an open window made it look as if a gust had blown the bacon away",
        twist="the bacon was not stolen at all; it had slid into the cape rack when the alarm rang",
        reveal="the cape rack held the bacon wrapped inside a folded red lining",
        misunderstanding="Bolt thought Penny had hidden the tray for a prank, and Penny thought Bolt had blamed her on purpose",
        reconciliation="Nova asked both friends to explain what they saw, then helped them say sorry and listen",
        fix="removed the bacon from the cape lining, wiped the tray clean, and set a safer breakfast shelf above the lockers",
        proof="the bacon tray stayed put, the cape rack was empty, and everybody could reach breakfast without a chase",
        ending="By the end, the breakfast bell rang over a neat tray, and the team ate together in the bright kitchen.",
        lesson="A twist can change the meaning of a clue, and a calm talk can turn blame into teamwork.",
    ),
    Case(
        mission="finish patrol before the city woke up",
        trouble="the bacon disappeared from the heat-safe box next to the stove",
        clue="one snapped rubber band and a speck of pepper on the floor",
        false_lead="the locked window made everyone stare at the street below",
        twist="the bacon had been removed from the box by the hero earlier and placed on the roof to cool",
        reveal="a whole strip waited on the rooftop beside a comic book and a flashlight",
        misunderstanding="Penny accused Bolt of sneaking the food away, while Bolt felt too shy to admit he had seen Nova move it",
        reconciliation="Nova told the truth first, and the others agreed that honesty mattered more than being right",
        fix="brought the bacon back inside, relocked the box, and added a reminder note for cooling food",
        proof="the safe box was closed, the roof was empty, and the team knew where breakfast belonged",
        ending="Soon the heroes were laughing at the table, with the bacon back where every hungry helper could reach it.",
        lesson="Truth works best when it is shared before suspicion grows.",
    ),
    Case(
        mission="keep the hero clubhouse ready for visitors",
        trouble="the bacon was missing from the silver plate after the alarm test",
        clue="a red button stuck to a kitchen glove and a faint smell of toast",
        false_lead="a shadow near the pantry made it seem like a burglar had come in",
        twist="the so-called shadow was only a laundry cape draped over a chair",
        reveal="the bacon had been removed and stored in a lunch box so the alarm test would not set off the smoke detector",
        misunderstanding="Bolt thought Penny had eaten the bacon, and Penny thought Bolt had played a joke by hiding it",
        reconciliation="Nova gathered the three friends, and they shared the story in order until the mistake made sense",
        fix="moved the bacon back to the silver plate, wrote a label for safe storage, and opened the windows a little wider",
        proof="the plate shone, the lunch box was marked, and the alarm test no longer caused confusion",
        ending="The clubhouse looked calm again, and the rescued breakfast glowed warm under the kitchen light.",
        lesson="When a problem has a safety reason, everyone should hear the reason before they guess.",
    ),
    Case(
        mission="prepare the team for a rescue drill",
        trouble="the bacon vanished from the warming drawer right before the drill began",
        clue="tiny crumbs on the drawer handle and a smudge of mustard on a glove",
        false_lead="the villain's blaring siren from outside sounded like proof of a break-in",
        twist="the villain was not in the kitchen at all; it was only a recorded siren from the practice speaker",
        reveal="the bacon had been removed by Penny and placed in a lunch tin to keep it from burning",
        misunderstanding="Bolt believed Penny had taken the bacon for herself, while Penny thought Bolt had ignored her warning",
        reconciliation="Nova asked them to repeat the timing of each step, then helped them apologize and shake hands",
        fix="put the bacon back in the warming drawer for one minute, then served it on plates when the drill ended",
        proof="the drawer shut smoothly, the speaker turned off, and the team could finish the drill without another mix-up",
        ending="After the siren faded, the friends shared the bacon and smiled at the tidy kitchen they had saved together.",
        lesson="A careful explanation can remove fear just as well as it removes a problem.",
    ),
    Case(
        mission="start the rooftop watch with full stomachs",
        trouble="the bacon disappeared from the picnic box on the fire escape",
        clue="a sticky fingerprint on the latch and a gust of warm grease smell",
        false_lead="the stairwell door swinging open looked like the work of a sneaky foe",
        twist="the door had been opened by the wind, not by a thief",
        reveal="the bacon sat on a nearby windowsill, where Nova had removed it from the hot box to cool",
        misunderstanding="Penny assumed Bolt had taken the food without asking, and Bolt worried Penny would be angry forever",
        reconciliation="Nova translated each person's worry into plain words so they could hear one another kindly",
        fix="moved the bacon into a covered basket, shut the picnic box, and brought clean napkins to the roof",
        proof="the basket stayed covered, the lid latched, and the rooftop watch began without any more blaming",
        ending="Under the morning sky, the heroes ate in peace while the city woke below them.",
        lesson="Sometimes reconciliation begins when someone helps the others understand what they were really afraid of.",
    ),
    Case(
        mission="clean up after a pancake flip contest",
        trouble="the bacon vanished from the serving tray during the last flip",
        clue="a curved trail of syrup from the counter to the sink",
        false_lead="a cracked window suggested the bacon had fallen outside",
        twist="the bacon had landed inside the apron pocket of the fastest helper",
        reveal="Penny found the bacon tucked in a pocket with the spatula handle still warm",
        misunderstanding="Bolt accused Penny of hoarding the bacon, but Penny had only tried to save it from the floor",
        reconciliation="Nova invited both friends to tell the story again, slower this time, until the truth was clear",
        fix="washed the apron, returned the bacon to the tray, and started a second contest with safer flipping rules",
        proof="the tray was full, the pocket was empty, and the second contest ended with no missing food",
        ending="The kitchen rang with laughter as the team ate the rescued bacon and cleaned up side by side.",
        lesson="If a clue can be explained two ways, the kindest choice is to ask before accusing.",
    ),
    Case(
        mission="guard the invention lab before school",
        trouble="the bacon disappeared from the warming shelf beside the gadget bench",
        clue="a bright sticker stuck to the underside of the shelf",
        false_lead="the villain's black cape hanging on a hook looked suspicious",
        twist="the cape was a lab curtain, and the missing bacon had been moved to cool by Nova",
        reveal="the bacon was hidden safely under a fan so it would not steam the blueprints",
        misunderstanding="Bolt thought Nova had forgotten the breakfast plan, and Penny thought Bolt was hiding the tray",
        reconciliation="Nova admitted the change, Bolt apologized for jumping to conclusions, and Penny forgave the worry",
        fix="returned the bacon to the shelf after cooling, then taped up a note that said 'Move food only with the team.'",
        proof="the shelf held the tray, the blueprints stayed clean, and the fan hummed softly beside the lunch box",
        ending="With the misunderstanding gone, the team marched into school together, cheerful and fed.",
        lesson="A plan becomes better when the people in it can forgive and adjust.",
    ),
    Case(
        mission="welcome a class tour to the hero tower",
        trouble="the bacon vanished from the kitchen plate right after the elevator dinged",
        clue="a trail of pepper flakes leading to the costume room",
        false_lead="the elevator ding made everyone think a stranger had arrived",
        twist="the stranger was only a delivery bot dropping off clean socks",
        reveal="the bacon had been removed to a warming pan while Nova answered the door",
        misunderstanding="Penny felt sure Bolt had eaten the bacon, and Bolt felt upset that nobody asked him first",
        reconciliation="Nova asked the two to look at the warming pan together, then guided them through a fair apology",
        fix="put the bacon back on the plate, added a timer to the warming pan, and served the tour snacks on schedule",
        proof="the plate was full again, the timer beeped once, and the visitors saw a team that solved problems kindly",
        ending="The class tour ended with smiling faces, and the bacon tray shone under the tower lights.",
        lesson="Fair questions are stronger than quick blame.",
    ),
    Case(
        mission="prepare a celebration snack for the neighborhood fair",
        trouble="the bacon disappeared from the blue tray beside the lemonade jug",
        clue="one paw-print in flour and a tiny scrap of paper towel",
        false_lead="the fair banner flapping in the wind seemed like a clue from a rival hero",
        twist="the banner had only blown against the window; the real change was that the bacon had been removed for safety",
        reveal="the bacon rested in a cool pan under the sink, exactly where Nova had put it to keep it from getting soggy",
        misunderstanding="Bolt thought Penny had taken the food to the craft table, while Penny thought Bolt had set a trap",
        reconciliation="Nova brought the pan out, explained the cooling step, and asked the others to forgive the confusion",
        fix="returned the bacon to the tray, dried the plate, and covered the food until the fair began",
        proof="the tray stayed dry, the pan was labeled, and the celebration snack was ready at last",
        ending="When the fair music started, the team shared the bacon and walked out together, proud and reconciled.",
        lesson="If people know why a thing moved, they can stop turning it into a mystery.",
    ),
]


@dataclass
class World:
    hero: Entity
    partner: Entity
    sidekick: Entity
    villain: Entity
    bacon: Entity
    tray: Entity
    kitchen: Entity
    roof: Entity
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def new_entity(eid: str, kind: str, type_: str, label: str, phrase: str = "") -> Entity:
    return Entity(id=eid, kind=kind, type=type_, label=label, phrase=phrase)


def build_world(params: StoryParams) -> World:
    hero = new_entity(params.hero, "character", "hero", "the hero", "a brave young superhero")
    partner = new_entity(params.partner, "character", "hero", "the partner", "a brave teammate")
    sidekick = new_entity(params.sidekick, "character", "hero", "the sidekick", "a quick-thinking helper")
    villain = new_entity(params.villain, "character", "villain", "the villain", "a comic-book trickster")
    bacon = new_entity("bacon", "thing", "food", "bacon", "a warm plate of bacon")
    tray = new_entity("tray", "thing", "tray", "tray", "a shiny breakfast tray")
    kitchen = new_entity("kitchen", "place", "room", "kitchen", "the tower kitchen")
    roof = new_entity("roof", "place", "roof", "roof", "the sunny roof")
    return World(hero=hero, partner=partner, sidekick=sidekick, villain=villain, bacon=bacon, tray=tray, kitchen=kitchen, roof=roof)


def tell(params: StoryParams) -> World:
    world = build_world(params)
    case = CASES[params.twist % len(CASES)]
    h, p, s, v = world.hero, world.partner, world.sidekick, world.villain
    bacon, tray = world.bacon, world.tray

    h.memes["worry"] += 1
    p.memes["teamwork"] += 1
    s.memes["hope"] += 1
    bacon.meters["missing"] = 1
    tray.meters["crumbs"] = 1

    openers = [
        f"At {SETTING}, {h.id}, {p.id}, and {s.id} were getting ready for {case.mission}.",
        f"The morning at {SETTING} began with capes, alarms, and a promise to finish {case.mission}.",
        f"Inside the hero kitchen, the team was busy with {case.mission} when trouble hit.",
        f"Before school and before patrol, {h.id}'s team had one important job: {case.mission}.",
    ]
    world.say(openers[params.twist % len(openers)])
    world.say(f"Then {case.trouble}.")
    world.say(f"{v.id} was nearby, so the missing breakfast felt like a real superhero case.")

    world.para()
    world.say(f"{h.id} spotted {case.clue}, but {case.false_lead}.")
    world.say(f"{h.id} whispered, 'We should not guess. Let's follow the clue that actually changed.'")
    world.say(f"{p.id} nodded and said, 'I can check the kitchen while you look near the roof.'")
    world.say(f"{s.id} added, 'And I will keep track of what we really know.'")

    world.para()
    world.say(f"The first surprise was a twist: {case.twist}.")
    world.say(f"That led the team to the answer, because {case.reveal}.")
    bacon.meters["missing"] = 0
    bacon.carried_by = h.id
    bacon.memes["relief"] += 1

    world.say(f"{p.id} frowned and said, '{case.misunderstanding}'")
    world.say(f"{h.id} looked from one friend to the other and replied, 'Let's slow down and hear the whole story.'")
    world.say(f"{v.id} sighed and said, 'I can help explain what happened.'")

    world.para()
    world.say(f"In the end, the team chose reconciliation: {case.reconciliation}.")
    world.say(f"Together they {case.fix}.")
    world.say(f"They checked the result, and {case.proof}.")
    world.say(f"{h.id} smiled and said, 'A real hero fixes the problem and the feelings too.'")
    world.say(f"{p.id} and {s.id} agreed, and even {v.id} looked relieved.")

    world.para()
    world.say(case.ending)
    world.say(f"The lesson was clear: {case.lesson}")

    world.facts.update(
        hero=h,
        partner=p,
        sidekick=s,
        villain=v,
        bacon=bacon,
        tray=tray,
        case=case,
        resolved=True,
        setting=SETTING,
        twist=params.twist,
        reconciliation_style=params.reconciliation_style,
    )
    return world


def story_qa(world: World) -> list[QAItem]:
    case: Case = world.facts["case"]
    h = world.facts["hero"]
    p = world.facts["partner"]
    s = world.facts["sidekick"]
    v = world.facts["villain"]
    return [
        QAItem(
            question="What problem started the story?",
            answer=f"The bacon disappeared from the breakfast tray, which stopped the team from starting {case.mission}.",
        ),
        QAItem(
            question="What clue helped the hero team?",
            answer=f"They followed {case.clue}, because that clue matched what really changed in the kitchen.",
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that {case.twist}",
        ),
        QAItem(
            question="How did the team reconcile?",
            answer=f"{h.id}, {p.id}, {s.id}, and even {v.id} talked it through calmly, apologized, and worked together to fix the breakfast problem.",
        ),
        QAItem(
            question="What changed by the end?",
            answer=f"The bacon was back, the tray was safe, and the team finished the morning together with less blame and more trust.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a superhero?",
            answer="A superhero is a character who uses courage, skill, and good choices to help others.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change that makes the story's meaning different from what readers first expected.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people who were upset talk kindly, forgive, and become friendly again.",
        ),
        QAItem(
            question="What does 'remove' mean?",
            answer="To remove something means to take it away from where it was.",
        ),
        QAItem(
            question="What is bacon?",
            answer="Bacon is a salty breakfast food made from pork that is often cooked until crisp.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a child-friendly superhero story set in {SETTING} where bacon goes missing and the team must {world.facts['case'].fix}.",
        "Include a clear twist, a clue, and a reconciliation scene with spoken dialogue that changes what the characters know.",
        "Keep the tone bright and heroic, with a concrete ending image proving the breakfast problem was solved.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in [world.hero, world.partner, world.sidekick, world.villain, world.bacon, world.tray, world.kitchen, world.roof]:
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(superhero_story).
requires(superhero_story, bacon).
requires(superhero_story, remove).
requires(superhero_story, twist).
requires(superhero_story, reconciliation).

valid_story(S) :- setting(S), requires(S, bacon), requires(S, remove), requires(S, twist), requires(S, reconciliation).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy import
    return "\n".join(
        [
            asp.fact("setting", "superhero_story"),
            asp.fact("requires", "superhero_story", "bacon"),
            asp.fact("requires", "superhero_story", "remove"),
            asp.fact("requires", "superhero_story", "twist"),
            asp.fact("requires", "superhero_story", "reconciliation"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp  # lazy import
    models = asp.one_model(asp_program("#show valid_story/1."))
    ok = any(atom.name == "valid_story" for atom in models)
    if ok:
        print("OK: ASP rules recognize the superhero breakfast story domain.")
        return 0
    print("MISMATCH: ASP rules failed to recognize the story domain.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small superhero story world with bacon, a twist, and reconciliation.")
    ap.add_argument("--hero", default=None)
    ap.add_argument("--partner", default=None)
    ap.add_argument("--sidekick", default=None)
    ap.add_argument("--villain", default=None)
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


def resolve_params(args: argparse.Namespace, rng: random.Random, sample_seed: int, base_seed: int) -> StoryParams:
    hero = args.hero or rng.choice(["Nova", "Spark", "Arrow", "Mira", "Quill"])
    partner = args.partner or rng.choice(["Bolt", "Comet", "Flare", "Ridge", "Juno"])
    sidekick = args.sidekick or rng.choice(["Penny", "Zip", "Moss", "Tuck", "Bea"])
    villain = args.villain or rng.choice(["Dr. Crisp", "The Hush", "Captain Fog", "Lady Static"])
    names = [hero, partner, sidekick, villain]
    if len(set(names)) != len(names):
        raise StoryError("All four characters must be different.")
    offset = sample_seed - base_seed
    return StoryParams(
        hero=hero,
        partner=partner,
        sidekick=sidekick,
        villain=villain,
        twist=offset % len(CASES),
        reconciliation_style=(offset // len(CASES)) % 4,
        seed=sample_seed,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


CURATED = [
    StoryParams(hero="Nova", partner="Bolt", sidekick="Penny", villain="Dr. Crisp"),
    StoryParams(hero="Spark", partner="Comet", sidekick="Zip", villain="The Hush"),
    StoryParams(hero="Mira", partner="Ridge", sidekick="Bea", villain="Captain Fog"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        print("ASP model:", [str(a) for a in model])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            sample_seed = base_seed + i
            params = resolve_params(args, random.Random(sample_seed), sample_seed, base_seed)
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
