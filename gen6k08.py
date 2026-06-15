"""
gen6k08.py - Coverage push #08 for gen6.

Sampled from the highest-frequency missing names after the 90% pass. These are
long-tail everyday actions, states, and structural wrappers. The implementations
are deliberately tolerant: they preserve phase kwargs through meta_story, honor
explicit focus kwargs through gen6k07 helpers, and avoid leaking child sentences
into noun slots.
"""

from __future__ import annotations

from typing import Any

from gen6 import (
    REGISTRY,
    World,
    Entity,
    NLGUtils,
    child_sentences,
    coherent,
    meta_story,
    is_meta_call,
)
from gen6k03 import _split, _phrases, _kw_targets, _cap
from gen6k07 import _actor_from, _kw_values, _concepts, _sentences, _clean_sentence


def _targets(chars: list[Entity], rest: list[Any], kw: dict, *keys: str) -> str:
    return _concepts(chars[1:] + rest + _kw_targets(kw) + _kw_values(kw, *keys))


def _register_action(name: str, past: str, *, solo: str = "something",
                     meme: str = "", amount: float = 0.3,
                     prep: str = "") -> None:
    def fn(ctx: World, *args: Any, **kw: Any) -> str:
        chars, rest = _split(args)
        actor = _actor_from(ctx, chars, kw)
        if actor is not None and is_meta_call(kw):
            body = meta_story(ctx, actor, kw)
            if body:
                return body
        sents = _sentences(rest + list(kw.values()))
        target = _targets(chars, rest, kw, "item", "object", "target", "goal")
        if actor is not None:
            if meme:
                actor.add_meme(meme, amount)
            ctx.actor = actor
            tail = f" {prep} {target}" if prep and target else (f" {target}" if target else "")
            lead = f"{ctx.say(actor)} {past}{tail}." if target else f"{ctx.say(actor)} {past} {solo}."
            return coherent(ctx, actor, [lead] + sents)
        if sents:
            return " ".join(sents)
        return f"Someone {past} {target}." if target else f"{_cap(name)} happened."
    fn.__name__ = name
    REGISTRY.kernel(name)(fn)


def _register_state(name: str, template: str, *, meme: str = "",
                    amount: float = 0.5) -> None:
    def fn(ctx: World, *args: Any, **kw: Any) -> str:
        chars, rest = _split(args)
        actor = _actor_from(ctx, chars, kw)
        if actor is not None and is_meta_call(kw):
            body = meta_story(ctx, actor, kw)
            if body:
                return body
        target = _targets(chars, rest, kw, "feeling", "about", "reason", "result")
        if actor is not None:
            if meme:
                actor.add_meme(meme, amount)
            ctx.actor = actor
            return _clean_sentence(template.format(s=ctx.say(actor), t=target))
        subject = _cap(target) if target else "Everyone"
        return _clean_sentence(template.format(s=subject, t=""))
    fn.__name__ = name
    REGISTRY.kernel(name)(fn)


def _register_meta(name: str, fallback: str, *, meme: str = "") -> None:
    def fn(ctx: World, *args: Any, **kw: Any) -> str:
        chars, rest = _split(args)
        actor = _actor_from(ctx, chars, kw)
        if actor is not None:
            if meme:
                actor.add_meme(meme, 0.4)
            ctx.actor = actor
            body = meta_story(ctx, actor, kw)
            sents = _sentences(rest)
            lead = fallback.format(s=ctx.say(actor))
            lead_sentence = _clean_sentence(f"{lead}.")
            if body:
                return coherent(ctx, actor, [lead_sentence, body])
            if sents:
                return coherent(ctx, actor, [lead_sentence] + sents)
            target = _targets(chars, rest, kw, "setting", "location", "activity", "item")
            return lead + (f" with {target}." if target else ".")
        sents = _sentences(rest + list(kw.values()))
        if sents:
            return " ".join(sents)
        target = _concepts(rest + _kw_targets(kw))
        return f"{_cap(name)} happened with {target}." if target else f"{_cap(name)} happened."
    fn.__name__ = name
    REGISTRY.kernel(name)(fn)


@REGISTRY.kernel("Setting")
def Setting(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    actor = _actor_from(ctx, chars, kw)
    place = _concepts(chars[1:] + rest + _kw_values(kw, "place", "location", "setting"))
    if actor is not None:
        ctx.actor = actor
        return f"{ctx.say(actor)} was in {place}." if place else f"{ctx.say(actor)} was there."
    return f"The story took place in {place}." if place else "The setting was clear."


@REGISTRY.kernel("Room")
def Room(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    actor = _actor_from(ctx, chars, kw)
    contents = _targets(chars, rest, kw, "contents", "items")
    if actor is not None:
        ctx.actor = actor
        return f"{ctx.say(actor)} was in the room with {contents}." if contents else f"{ctx.say(actor)} was in the room."
    return f"There was a room with {contents}." if contents else "There was a room."


@REGISTRY.kernel("News")
def News(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    actor = _actor_from(ctx, chars, kw)
    topic = _targets(chars, rest, kw, "status", "message", "about")
    if actor is not None:
        actor.add_meme("Awareness", 0.3)
        ctx.actor = actor
        return f"{ctx.say(actor)} heard news about {topic}." if topic else f"{ctx.say(actor)} heard some news."
    return f"There was news about {topic}." if topic else "There was news."


@REGISTRY.kernel("Yes")
def Yes(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    actor = _actor_from(ctx, chars, kw)
    target = _targets(chars, rest, kw, "answer", "response")
    if actor is not None:
        actor.add_meme("Agreement", 0.4)
        ctx.actor = actor
        return f"{ctx.say(actor)} said yes to {target}." if target else f"{ctx.say(actor)} said yes."
    return f"Yes to {target}." if target else "Yes."


@REGISTRY.kernel("NoPlay")
def NoPlay(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    actor = _actor_from(ctx, chars, kw)
    target = _targets(chars, rest, kw, "game", "activity")
    if actor is not None:
        actor.add_meme("Refusal", 0.4)
        ctx.actor = actor
        return f"{ctx.say(actor)} could not play with {target}." if target else f"{ctx.say(actor)} could not play."
    return f"No one could play with {target}." if target else "There was no playing."


@REGISTRY.kernel("NotFound")
def NotFound(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    actor = _actor_from(ctx, chars, kw)
    target = _targets(chars, rest, kw, "item", "object", "target")
    if actor is not None:
        actor.add_meme("Sadness", 0.2)
        ctx.actor = actor
        return f"{ctx.say(actor)} could not find {target}." if target else f"{ctx.say(actor)} could not find it."
    return f"{_cap(target)} could not be found." if target else "It could not be found."


@REGISTRY.kernel("TooBig")
def TooBig(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    actor = _actor_from(ctx, chars, kw)
    target = _targets(chars, rest, kw, "object", "for")
    if actor is not None:
        ctx.actor = actor
        return f"{target} was too big for {ctx.say(actor)}." if target else f"It was too big for {ctx.say(actor)}."
    return f"{_cap(target)} was too big." if target else "It was too big."


@REGISTRY.kernel("Flood")
def Flood(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    actor = _actor_from(ctx, chars, kw)
    target = _targets(chars, rest, kw, "water", "target", "location")
    if actor is not None:
        actor.add_meme("Danger", 0.4)
        ctx.actor = actor
        return f"{ctx.say(actor)} saw flooding around {target}." if target else f"{ctx.say(actor)} saw a flood."
    return f"Water flooded {target}." if target else "There was a flood."


@REGISTRY.kernel("Lie")
def Lie(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    actor = _actor_from(ctx, chars, kw)
    claim = _targets(chars, rest, kw, "claim", "about", "object")
    if actor is not None:
        actor.add_meme("Dishonesty", 0.5)
        ctx.actor = actor
        return f"{ctx.say(actor)} lied about {claim}." if claim else f"{ctx.say(actor)} lied."
    return f"There was a lie about {claim}." if claim else "There was a lie."


@REGISTRY.kernel("HelpRequest")
def HelpRequest(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    actor = _actor_from(ctx, chars, kw)
    target = _targets(chars, rest, kw, "to", "from", "target", "object")
    if actor is not None:
        actor.add_meme("Need", 0.4)
        ctx.actor = actor
        return f"{ctx.say(actor)} asked {target} for help." if target else f"{ctx.say(actor)} asked for help."
    return f"Someone asked {target} for help." if target else "Someone asked for help."


for _name, _template, _meme in [
    ("Fearful", "{s} felt fearful about {t}.", "Fear"),
    ("Hot", "{s} was hot.", "Heat"),
    ("Betrayal", "{s} felt betrayed by {t}.", "Betrayal"),
    ("Thought", "{s} thought about {t}.", "Reflection"),
    ("Passion", "{s} felt passion for {t}.", "Desire"),
    ("Tragedy", "{s} faced a tragedy with {t}.", "Sadness"),
    ("Strength", "{s} found strength in {t}.", "Strength"),
    ("Defeat", "{s} defeated {t}.", "Victory"),
    ("Ability", "{s} gained the ability for {t}.", "Skill"),
    ("Quiet", "{s} was quiet about {t}.", "Quiet"),
    ("Fixed", "{s} was fixed.", "Repair"),
    ("Bright", "{s} was bright.", "Light"),
    ("Impatience", "{s} felt impatient about {t}.", "Impatience"),
    ("Strong", "{s} was strong.", "Strength"),
    ("Dark", "{s} was dark.", "Darkness"),
    ("Good", "{s} was good with {t}.", "Goodness"),
    ("Abundance", "{s} had plenty of {t}.", "Abundance"),
    ("Duty", "{s} had a duty to {t}.", "Duty"),
    ("Engaged", "{s} stayed engaged with {t}.", "Engagement"),
    ("Assurance", "{s} felt assured about {t}.", "Confidence"),
    ("Inside", "{s} was inside {t}.", "Place"),
    ("Companionship", "{s} had companionship with {t}.", "Friendship"),
    ("Power", "{s} felt powerful with {t}.", "Power"),
    ("Dilemma", "{s} faced a dilemma about {t}.", "Choice"),
    ("Alternative", "{s} found an alternative to {t}.", "Choice"),
    ("Obedient", "{s} was obedient about {t}.", "Obedience"),
    ("Improvement", "{s} improved at {t}.", "Growth"),
    ("Tradition", "{s} followed a tradition with {t}.", "Routine"),
    ("Provision", "{s} had provision for {t}.", "Care"),
    ("Disturbance", "{s} was disturbed by {t}.", "Disruption"),
    ("Chaos", "{s} faced chaos with {t}.", "Chaos"),
    ("Weather", "{s} noticed the weather: {t}.", "Weather"),
    ("Enjoyment", "{s} enjoyed {t}.", "Joy"),
    ("Sharp", "{s} was sharp.", "Danger"),
    ("Barrier", "{s} faced a barrier with {t}.", "Obstacle"),
    ("Affirmation", "{s} felt affirmed by {t}.", "Confidence"),
    ("Obstacles", "{s} faced obstacles: {t}.", "Obstacle"),
    ("Defense", "{s} defended {t}.", "Protection"),
    ("EverAfter", "{s} lived happily ever after with {t}.", "Joy"),
    ("Continuity", "{s} continued with {t}.", "Persistence"),
    ("Trapped", "{s} was trapped by {t}.", "Danger"),
    ("Miracle", "{s} witnessed a miracle with {t}.", "Awe"),
    ("Healthy", "{s} was healthy.", "Health"),
    ("Leak", "{s} noticed a leak in {t}.", "Problem"),
    ("Empowerment", "{s} felt empowered by {t}.", "Confidence"),
    ("Ownership", "{s} had ownership of {t}.", "Possession"),
    ("Inciting", "{s} faced an inciting moment with {t}.", "Catalyst"),
    ("Fearless", "{s} was fearless about {t}.", "Brave"),
    ("Hard", "{s} was hard.", "Difficulty"),
    ("Delicious", "{s} tasted delicious.", "Joy"),
    ("Closure", "{s} found closure with {t}.", "Ending"),
    ("Complete", "{s} was complete.", "Completion"),
    ("More", "{s} wanted more of {t}.", "Desire"),
    ("Interest", "{s} was interested in {t}.", "Curiosity"),
    ("Admiration", "{s} admired {t}.", "Awe"),
    ("Purpose", "{s} found purpose in {t}.", "Purpose"),
    ("Exhaustion", "{s} felt exhausted by {t}.", "Fatigue"),
    ("Bonded", "{s} bonded with {t}.", "Friendship"),
    ("Conclusion", "{s} reached a conclusion about {t}.", "Ending"),
    ("Strengthened", "{s} was strengthened by {t}.", "Strength"),
    ("Defiance", "{s} showed defiance about {t}.", "Willpower"),
    ("Ignored", "{s} felt ignored by {t}.", "Sadness"),
    ("Uncertainty", "{s} felt uncertain about {t}.", "Confusion"),
    ("Restored", "{s} was restored.", "Repair"),
    ("Weak", "{s} felt weak.", "Weakness"),
    ("Truth", "{s} learned the truth about {t}.", "Truth"),
    ("Craving", "{s} craved {t}.", "Desire"),
    ("Loyalty", "{s} showed loyalty to {t}.", "Love"),
    ("Over", "{s} went over {t}.", "Movement"),
    ("Awakening", "{s} awakened to {t}.", "Awareness"),
    ("Triumph", "{s} triumphed over {t}.", "Victory"),
    ("Risk", "{s} faced a risk with {t}.", "Danger"),
    ("Harm", "{s} was harmed by {t}.", "Pain"),
    ("Responsible", "{s} was responsible for {t}.", "Responsibility"),
    ("Better", "{s} got better with {t}.", "Recovery"),
    ("Friendly", "{s} was friendly with {t}.", "Friendship"),
    ("Thankful", "{s} felt thankful for {t}.", "Gratitude"),
    ("Sour", "{s} tasted sour.", "Disgust"),
    ("Filthy", "{s} was filthy.", "Mess"),
    ("Vision", "{s} had a vision of {t}.", "Imagination"),
    ("Skilled", "{s} was skilled at {t}.", "Skill"),
    ("Unable", "{s} was unable to {t}.", "Limitation"),
    ("Colorful", "{s} was colorful.", "Beauty"),
    ("Path", "{s} followed a path to {t}.", "Journey"),
    ("Connected", "{s} felt connected with {t}.", "Friendship"),
    ("Fulfillment", "{s} found fulfillment in {t}.", "Joy"),
    ("Beautiful", "{s} was beautiful.", "Beauty"),
] :
    _register_state(_name, _template, meme=_meme)


for _name, _template, _meme in [
    ("Destruction", "{s} faced destruction from {t}.", "Danger"),
    ("Medicine", "{s} had medicine for {t}.", "Health"),
    ("Repetition", "{s} repeated {t}.", "Practice"),
    ("Effect", "{s} saw the effect of {t}.", "Consequence"),
    ("Avoidance", "{s} avoided {t}.", "Caution"),
    ("Disagreement", "{s} disagreed about {t}.", "Conflict"),
    ("Perseverance", "{s} persevered through {t}.", "Persistence"),
    ("Innovation", "{s} found a new idea for {t}.", "Creativity"),
    ("Intrusion", "{s} faced an intrusion from {t}.", "Disruption"),
    ("Dispute", "{s} had a dispute about {t}.", "Conflict"),
    ("Rot", "{s} noticed rot in {t}.", "Decay"),
    ("Hate", "{s} hated {t}.", "Anger"),
    ("Escalation", "{s} felt things escalate with {t}.", "Conflict"),
    ("Bag", "{s} had a bag for {t}.", "Possession"),
    ("Reason", "{s} had a reason for {t}.", "Thought"),
    ("Collision", "{s} had a collision with {t}.", "Impact"),
    ("Symbol", "{s} saw a symbol of {t}.", "Meaning"),
    ("Puzzle", "{s} faced a puzzle about {t}.", "Problem"),
    ("Imitation", "{s} copied {t}.", "Learning"),
    ("Remedy", "{s} found a remedy for {t}.", "Healing"),
    ("Mood", "{s} was in a mood about {t}.", "Emotion"),
    ("Missed", "{s} missed {t}.", "Loss"),
    ("Authority", "{s} faced authority over {t}.", "Authority"),
    ("BadEnding", "{s} reached a sad ending with {t}.", "Sadness"),
    ("Limitation", "{s} faced a limitation with {t}.", "Limitation"),
    ("Caretaking", "{s} cared for {t}.", "Care"),
    ("Renewal", "{s} found renewal in {t}.", "Growth"),
    ("Info", "{s} learned information about {t}.", "Awareness"),
    ("Appearance", "{s} noticed the appearance of {t}.", "Awareness"),
    ("Selfish", "{s} acted selfish about {t}.", "Selfishness"),
    ("Moderation", "{s} used moderation with {t}.", "Restraint"),
    ("Fragile", "{s} was fragile around {t}.", "Vulnerability"),
    ("Creative", "{s} was creative with {t}.", "Creativity"),
    ("Loud", "{s} was loud about {t}.", "Noise"),
    ("Stubborn", "{s} was stubborn about {t}.", "Willpower"),
    ("Busy", "{s} was busy with {t}.", "Activity"),
    ("Slow", "{s} was slow with {t}.", "Delay"),
    ("Forever", "{s} remembered {t} forever.", "Memory"),
    ("Emergency", "{s} faced an emergency with {t}.", "Danger"),
    ("Disapproval", "{s} disapproved of {t}.", "Judgment"),
    ("SafePlay", "{s} played safely with {t}.", "Safety"),
    ("Cost", "{s} saw the cost of {t}.", "Tradeoff"),
    ("Parting", "{s} had to part from {t}.", "Farewell"),
    ("Metamorphosis", "{s} changed through {t}.", "Transformation"),
] :
    _register_state(_name, _template, meme=_meme)


for _name, _past, _solo, _meme in [
    ("Deal", "made a deal with", "someone", "Agreement"),
    ("TurnOff", "turned off", "something", "Action"),
    ("Stumble", "stumbled over", "something", "Surprise"),
    ("Yield", "yielded", "the way", "Acceptance"),
    ("Appeal", "appealed to", "someone", "Communication"),
    ("SlideDown", "slid down", "the slide", "Joy"),
    ("Rip", "ripped", "something", "Damage"),
    ("Disappear", "disappeared from", "sight", "Loss"),
    ("Giggle", "giggled at", "something", "Joy"),
    ("Lay", "laid", "something", "Action"),
    ("Solve", "solved", "the problem", "Wisdom"),
    ("Secure", "secured", "it", "Protection"),
    ("Showoff", "showed off", "something", "Pride"),
    ("Tour", "toured", "the place", "Curiosity"),
    ("Spell", "spelled", "the word", "Learning"),
    ("Retry", "tried again with", "it", "Persistence"),
    ("Supply", "supplied", "what was needed", "Care"),
    ("Shape", "shaped", "something", "Creativity"),
    ("Sniff", "sniffed", "around", "Curiosity"),
    ("Score", "scored", "a point", "Victory"),
    ("Set", "set", "it up", "Preparation"),
    ("Twirl", "twirled", "around", "Joy"),
    ("Preserve", "preserved", "it", "Care"),
    ("Identify", "identified", "it", "Awareness"),
    ("Lend", "lent", "something", "Kindness"),
    ("Think", "thought about", "it", "Reflection"),
    ("Confession", "confessed", "the truth", "Truth"),
    ("Live", "lived with", "others", "Life"),
    ("Comment", "commented on", "it", "Communication"),
    ("TakeHome", "took home", "something", "Care"),
    ("Urge", "urged", "someone", "Desire"),
    ("Insert", "inserted", "it", "Action"),
    ("Complaint", "complained about", "it", "Frustration"),
    ("Inspect", "inspected", "it", "Curiosity"),
    ("Accusation", "accused", "someone", "Conflict"),
    ("Hunt", "hunted for", "something", "Search"),
    ("Strike", "struck", "something", "Conflict"),
    ("Critique", "critiqued", "it", "Judgment"),
    ("Equip", "equipped", "it", "Preparation"),
    ("Punish", "punished", "someone", "Authority"),
    ("Imitate", "imitated", "someone", "Learning"),
    ("Sprint", "sprinted toward", "ahead", "Energy"),
    ("Sew", "sewed", "carefully", "Skill"),
    ("Resume", "resumed", "the activity", "Continuation"),
    ("Relax", "relaxed near", "there", "Peace"),
    ("Launch", "launched", "it", "Action"),
    ("Query", "asked about", "it", "Curiosity"),
    ("Own", "owned", "it", "Possession"),
    ("Understand", "understood", "it", "Wisdom"),
    ("Demonstration", "demonstrated", "it", "Teaching"),
    ("Propose", "proposed", "an idea", "Idea"),
    ("Cast", "cast", "it", "Action"),
    ("Forgot", "forgot", "something", "Forgetfulness"),
    ("Distract", "distracted", "someone", "Distraction"),
    ("Arrange", "arranged", "things", "Order"),
    ("Unite", "united", "everyone", "Friendship"),
    ("Defend", "defended", "someone", "Protection"),
    ("Recognize", "recognized", "it", "Awareness"),
    ("Decline", "declined", "the offer", "Refusal"),
    ("Act", "acted like", "someone", "Play"),
    ("Abandon", "abandoned", "it", "Loss"),
    ("Tug", "tugged on", "it", "Effort"),
    ("StayClose", "stayed close to", "someone", "Safety"),
    ("Consider", "considered", "it", "Reflection"),
    ("Insist", "insisted to", "someone", "Willpower"),
    ("Depart", "departed from", "there", "Farewell"),
] :
    _register_action(_name, _past, solo=_solo, meme=_meme)


for _name, _past, _solo, _meme in [
    ("Applause", "applauded", "warmly", "Joy"),
    ("Like", "liked", "it", "Love"),
    ("Vow", "vowed to keep", "a promise", "Commitment"),
    ("Acquisition", "acquired", "something", "Possession"),
    ("Breath", "took a breath near", "there", "Calm"),
    ("Appreciate", "appreciated", "it", "Gratitude"),
    ("Dressup", "dressed up as", "someone", "Play"),
    ("KeepSafe", "kept safe", "someone", "Protection"),
    ("Smiles", "smiled at", "someone", "Joy"),
    ("Shut", "shut", "it", "Action"),
    ("Disagree", "disagreed with", "someone", "Conflict"),
    ("Prioritize", "prioritized", "what mattered", "Choice"),
    ("Consumption", "consumed", "something", "Need"),
    ("Exclaim", "exclaimed about", "it", "Surprise"),
    ("Lecture", "lectured about", "it", "Teaching"),
    ("Persist", "persisted through", "trouble", "Persistence"),
    ("Clear", "cleared", "the way", "Order"),
    ("Massage", "massaged", "gently", "Care"),
    ("Include", "included", "someone", "Friendship"),
    ("Select", "selected", "one", "Choice"),
    ("Reflect", "reflected on", "it", "Reflection"),
    ("Hatch", "hatched", "carefully", "Birth"),
    ("Activate", "activated", "it", "Action"),
    ("Ignite", "ignited", "it", "Fire"),
    ("EatAll", "ate all of", "it", "Food"),
    ("Possess", "possessed", "it", "Possession"),
    ("Embrace", "embraced", "someone", "Love"),
    ("Earn", "earned", "it", "Reward"),
    ("Loop", "went through", "a loop", "Repetition"),
] :
    _register_action(_name, _past, solo=_solo, meme=_meme)


for _name, _fallback, _meme in [
    ("TeaParty", "{s} had a tea party", "Joy"),
    ("SharedJoy", "{s} shared joy", "Joy"),
    ("Marriage", "{s} celebrated a marriage", "Love"),
    ("FriendshipStory", "{s} lived through a friendship story", "Friendship"),
    ("ReturnPlay", "{s} returned to play", "Joy"),
    ("Contest", "{s} entered a contest", "Competition"),
    ("ConflictResolution", "{s} worked through a conflict", "Agreement"),
    ("Playtime", "{s} had playtime", "Joy"),
    ("PretendPlay", "{s} played pretend", "Imagination"),
    ("Vacation", "{s} went on vacation", "Joy"),
    ("PlaySession", "{s} had a play session", "Joy"),
    ("SharedMeal", "{s} shared a meal", "Friendship"),
    ("MarketVisit", "{s} visited the market", "Need"),
    ("ProblemSolving", "{s} solved a problem", "Wisdom"),
    ("PlayfulAdventure", "{s} had a playful adventure", "Adventure"),
    ("PlayfulDay", "{s} had a playful day", "Joy"),
    ("BeachDay", "{s} spent a day at the beach", "Joy"),
    ("Holiday", "{s} had a holiday", "Joy"),
    ("ZooVisit", "{s} visited the zoo", "Curiosity"),
    ("Shopping", "{s} went shopping", "Need"),
    ("Fishing", "{s} went fishing", "Search"),
    ("RescueAttempt", "{s} attempted a rescue", "Brave"),
    ("Adoption", "{s} adopted something", "Care"),
    ("WishGrant", "{s} had a wish granted", "Joy"),
    ("CarefulPlay", "{s} played carefully", "Care"),
    ("Lunch", "{s} had lunch", "Food"),
    ("Counting", "{s} practiced counting", "Learning"),
    ("Naming", "{s} chose a name", "Identity"),
    ("Birth", "{s} witnessed a birth", "Life"),
] :
    _register_meta(_name, _fallback, meme=_meme)


for _name, _fallback, _meme in [
    ("FamilyTrip", "{s} went on a family trip", "Family"),
    ("DayOut", "{s} went out for the day", "Joy"),
    ("HelpAttempt", "{s} tried to help", "Kindness"),
] :
    _register_meta(_name, _fallback, meme=_meme)


if __name__ == "__main__":
    import gen6registry  # noqa: F401
    from gen6 import generate

    tests = [
        "Lily(Character, girl)\nFearful(spider) + Courage(Lily)",
        "Tim(Character, boy)\nContest(Tim, process=Run + Win)",
        "Mia(Character, girl)\nCooperation(participants=[Mia], process=Build(castle))",
        "Cat(Character, cat)\nNotFound(toy) + Retry(Search(toy))",
    ]
    for i, test in enumerate(tests, 1):
        print(f"--- TEST {i} ---")
        print(generate(test))
        print()
