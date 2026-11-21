"""Short semantic realizations, composed from typed phrases rather than stories.

None means an internal physical step. Those steps still execute, guard, and
replay; later scenes can aggregate only effects already recorded in that world.
"""
from .surface import SpeechLanguage, scene, claim
from ..portable.nouns import pronoun


def plan(w, f, tense="past", lexicon=None):
    g = SpeechLanguage(w, tense, lexicon)
    dispatch = {"rescue": recovery, "kite": recovery, "key": recovery,
                "music": music, "greenhouse": greenhouse, "library": library, "pottery": pottery}
    return dispatch[w.scenario](w, f, g)


def recovery(w, f, g):
    h, t, helper, tool = w.hero, w.target, w.helper, w.tool
    hero, other, target, instrument = (w.entities[x].noun for x in (h, helper, t, tool))
    n, r, v, s, pp = g.n, g.ref, g.v, g.s, g.pp
    place = w.entities[tool].location
    if f.kind == "notice":
        if w.scenario == "rescue":
            opening = s(n(target, "cold", det="a"), g.be(pp("on", n("ledge", "high", det="a"))))
            goal = v("rescue", r(t))
            problem = f"The {target} was on a high ledge. It was cold."
        elif w.scenario == "kite":
            opening = s(n("kite", det="a"), g.be("torn"))
            goal = v("repair", r(t))
            problem = "The kite was torn. It needed repair."
        else:
            opening = g.join(s(r("door"), g.be("locked")), s(r(t), g.be("missing")))
            goal = v("find", r(t))
            problem = "The door was locked. Its key was missing."
        speech = g.line(h, g.me(v("want", goal)), listener=helper if w.entities[helper].location == w.entities[h].location else None)
        return scene(opening, speech, qa=[
            claim("problem", "what", "What problem begins the story?", problem, t),
            claim("goal", "who", "Who wanted to solve the problem?", f"{hero} wanted to solve it. {hero} wanted to " +
                  {"rescue": f"rescue the {target}.", "kite": "repair the kite.", "key": "find the key."}[w.scenario], h, t)])
    if f.kind in {"think", "ask"}:
        if w.entities[helper].location == w.entities[h].location:
            content = s(r(tool), g.be(pp("in" if place != "porch" else "on", n(place))), tense="present")
            return scene(g.line(helper, content, listener=h), qa=[
                claim("tool_location", "where", f"Where was the {instrument}?",
                      f"The {instrument} was {'on' if place == 'porch' else 'in'} the {place}. {other} told {hero} where to find it.", tool, helper, h)])
        return scene(s(h, v("find", r(tool))))
    if f.kind == "attempt":
        if w.scenario == "rescue":
            return scene(s(h, g.can(v("reach", r(t))), negative=True))
        if w.scenario == "kite":
            return scene(s(r(t), g.adv(v("fall"), pp("on", n("grass")))))
        return scene(s(h, v("see", r(t)), negative=True))
    if f.kind == "solve":
        action = {"rescue": lambda: g.adv(v("lift", r(t)), "down"),
                  "kite": lambda: v("repair", r(t)),
                  "key": lambda: g.adv(v("find", r(t)), pp("under", n("bench")))}[w.scenario]()
        answer = {"rescue": f"{hero} used the ladder. {hero} lifted the {target} down.",
                  "kite": f"{hero} used tape. {hero} repaired the kite.",
                  "key": f"{hero} used a lantern. {hero} found the key under the bench."}[w.scenario]
        return scene(g.either(s(h, v("use", r(tool), action)), s(h, g.adv(action, pp("with", r(tool))))), qa=[
            claim("solution", "how", "How was the problem solved?", answer, h, t, tool)])
    if f.kind == "finish":
        if w.scenario == "rescue":
            return scene(s(h, g.adv(v("wrap", r(t)), pp("in", r("blanket", adjectives=("warm",))))), qa=[
                claim("care", "what", f"What did {hero} use to warm the {target}?",
                      f"{hero} wrapped the {target} in a blanket. The blanket was warm.", h, t, "blanket")])
        if w.scenario == "kite":
            return scene(s(h, g.adv(v("launch", r(t)), pp("in", n("wind")))), qa=[])
        return scene(s(h, g.adv(v("unlock", r("door")), pp("with", r(t)))), qa=[
            claim("unlock", "what", "What opened the way inside?", f"{hero} unlocked the door. The key was used to unlock it.", h, t, "door")])
    if f.kind == "ending":
        if w.scenario == "rescue":
            ending = s(r(t), g.adv(v("rest"), pp("in", r("blanket", adjectives=("warm",)))))
            answer = f"The {target} rested in the warm blanket. It was warm at the end."
        elif w.scenario == "kite":
            ending = s(r(t), g.adv(v("dance"), pp("in", n("sky"))))
            answer = "The kite danced in the sky. It could fly again."
        else:
            ending = s(h, g.adv(v("step"), pp("through", r("door", adjectives=("open",)))))
            answer = f"{hero} stepped through the door. The door was open."
        return scene(ending, qa=[claim("ending", "what_next", "What happened at the end?", answer, h, t)])
    return None


def music(w, f, g):
    n, r, v, s, pp = g.n, g.ref, g.v, g.s, g.pp
    if f.kind == "opening":
        return scene(s("hero", g.adv(v("hope", v("play", n("duet", det="a"))), pp("with", r("partner")))), qa=[
            claim("goal", "what", "What did Nia hope to do?", "Nia hoped to play a duet. She hoped to play with Mateo.", "hero", "partner")])
    if f.kind == "invite":
        return scene(g.line("hero", g.me(v("want", g.adv(v("play"), pp("with", pronoun("you"))))), listener="partner"))
    if f.kind == "decline":
        return scene(g.line("partner", g.me(g.be("ready"), negative=True), listener="hero"), qa=[
            claim("boundary", "who", "Who said they were not ready?", "Mateo said he was not ready. He told Nia.", "hero", "partner")])
    if f.kind == "signup":
        return scene(g.line("hero", g.me(v("choose", v("perform", n("solo", det="a")))), listener="partner")
                     if w.entities["partner"].location == w.entities["hero"].location else s("hero", v("choose", v("perform", n("solo", det="a")))),
                     qa=[claim("choice", "what", "What did Nia choose to perform?", "Nia chose a solo. She chose to perform on her own.", "hero")])
    if f.kind == "perform":
        return scene(g.using("hero", v("perform", n("solo")), r("drum")), qa=[
            claim("instrument", "how", "How did Nia perform her solo?", "Nia performed the solo on a drum. She performed on her own.", "hero", "drum")])
    if f.kind == "consent":
        return scene(g.line("partner", g.me(v("want", g.adv(v("play"), "privately", pp("with", pronoun("you"))))), listener="hero"), qa=[
            claim("consent", "what", "What did Mateo agree to do?", "Mateo said he wanted to play privately. He wanted to play with Nia.", "hero", "partner")])
    if f.kind == "decline_private":
        return scene(g.line("partner", g.me(g.be("ready"), negative=True), listener="hero"))
    if f.kind == "join":
        return scene(s(g.both(r("hero"), r("partner")), g.adv(v("play", n("duet", det="a")), "privately")), qa=[
            claim("outcome", "what_next", "What happened after the solo?", "Nia and Mateo played a duet. They played privately.", "hero", "partner")])
    if f.kind == "quiet":
        return scene(s("hero", v("accept", g.possess(r("partner"), g.cn("choice")))), qa=[
            claim("respect", "who", "Whose choice did Nia accept?", "Nia accepted Mateo's choice. She left the decision to him.", "hero", "partner")])
    if f.kind == "ending":
        drums = g.both(r("drum"), r("spare"))
        return scene(s(drums, g.be(pp("on", n("shelf")))), qa=[
            claim("return", "where", "Where were the instruments at the end?", "Both drums were on the shelf. Neither character was holding a drum then.", "drum", "spare")])
    return None


def greenhouse(w, f, g):
    n, r, v, s, pp = g.n, g.ref, g.v, g.s, g.pp
    if f.kind == "notice":
        return scene(s("hero", v("notice", r("tomatoes", adjectives=("thirsty",)))),
            g.line("caretaker", s(r("tap"), g.be("broken"), tense="present"), listener="hero"), qa=[
                claim("problem", "what", "What was wrong in the greenhouse?", "The tomato seedlings were thirsty. The tap was broken.", "tomatoes", "tap"),
                claim("speaker", "who", "Who explained the problem with the tap?", "Mr Bell said the tap was broken. He told Nia.", "caretaker", "hero", "tap")])
    if f.kind == "borrow":
        return scene(g.line("hero", g.me(g.can(v("water", r("tomatoes")))), listener="caretaker"))
    if f.kind == "water":
        if f.patient == "tomatoes":
            return scene(g.using("hero", v("water", r("tomatoes")), r("can")), qa=[
                claim("water", "how", "How did Nia water the seedlings?", "Nia used the watering can. She watered the tomato seedlings with it.", "hero", "tomatoes", "can")])
        return scene(s("hero", v("water", r("sunflower"))))
    if f.kind == "shade_break":
        return scene(s(r("cloth"), v("fall")))
    if f.kind == "secure":
        action = s("hero", g.adv(v("secure", r("umbrella")), pp("above", r("tomatoes")), pp("with", r("tie"))))
        return scene(g.join(action, s(r("tomatoes"), g.be("exposed")), "because"), qa=[
            claim("shade", "how", "How did Nia protect the seedlings after the cloth fell?", "Nia secured an umbrella above the seedlings. She used a garden tie.", "hero", "umbrella", "tomatoes", "tie"),
            claim("shade_reason", "why", "Why did Nia secure an umbrella above the seedlings?", "The seedlings were exposed. Nia secured an umbrella above them.", "hero", "tomatoes", "umbrella")])
    if f.kind == "repair_shade":
        return scene(g.using("owner", v("repair", r("cloth")), r("clip")), qa=[
            claim("repair", "who", "Who repaired the shade cloth?", "Mrs Okafor repaired it. She used a clip.", "owner", "cloth", "clip")])
    if f.kind == "repair_tap":
        return scene(s("caretaker", v("repair", r("tap"))))
    if f.kind == "return":
        return scene(s("hero", g.adv(v("return", r("can")), pp("to", r("caretaker")))), qa=[
            claim("return", "who", "Who got the watering can back?", "Nia returned the watering can to Mr Bell. Mr Bell had it again.", "hero", "caretaker", "can")])
    if f.kind == "ending":
        return scene(s(r("tomatoes"), g.adv(v("stand"), pp("under", r("cloth", adjectives=("repaired",))))), qa=[
            claim("ending", "where", "Where did the seedlings stand at the end?", "The seedlings stood under the shade cloth. The cloth was repaired.", "tomatoes", "cloth")])
    return None


def library(w, f, g):
    n, r, v, s, pp = g.n, g.ref, g.v, g.s, g.pp
    if f.kind == "wish":
        return scene(g.sequence("hero", v("hold", r("atlas", first=True)),
                                v("want", v("sketch", n("crater", det="bare", number="plural")))), qa=[
            claim("goal", "what", "What did Mina want to do?", "Mina wanted to sketch craters. She held a moon atlas.", "hero", "atlas")])
    if f.kind == "missing":
        return scene(g.line("friend", s(g.possess(pronoun("I"), g.cn("whale book")), g.be("missing"), tense="present"), listener="hero"),
                     g.line("hero", g.me(v("promise", v("help", pronoun("you")))), listener="friend"), qa=[
            claim("promise", "who", "Who promised to help Jun?", "Mina promised to help Jun. Jun had said his whale book was missing.", "hero", "friend", "book")])
    if f.kind == "failed_search":
        return scene(g.join(s(g.both(r("hero"), r("friend")), v("search", n("window nook"))),
                            s("hero", v("find", r("book")), negative=True), "but"), qa=[
            claim("failed_search", "where", "Where did the children search without finding the book?", "They did not find the book in the window nook. Mina and Jun searched there together.", "hero", "friend", "book")])
    if f.kind == "clue":
        return scene(g.either(s("friend", g.adv(v("spot", r("bookmark")), pp("on", n("high shelf")))),
                              s("friend", g.adv(v("see", r("bookmark")), pp("on", n("high shelf"))))), qa=[
            claim("clue", "what", "What clue did Jun spot?", "Jun spotted a star bookmark. It was on a high shelf.", "friend", "bookmark")])
    if f.kind == "reserve_atlas":
        return scene(s("helper", g.adv(v("save", r("atlas")), pp("for", r("hero")))), qa=[
            claim("atlas", "who", "Who saved the atlas for Mina?", "Ms Alvarez saved it for Mina. The atlas was set aside for her.", "helper", "atlas", "hero")])
    if f.kind == "release_atlas":
        return scene(g.join(s("hero", g.adv(v("return", r("atlas")), pp("to", n("display table")))),
                           s("hero", v("choose", v("help", r("friend"))))), qa=[
            claim("atlas", "why", "Why did Mina put her atlas back?", "Mina chose to help Jun. She returned the atlas to the display table.", "hero", "friend", "atlas")])
    if f.kind == "retrieve":
        return scene(g.using("helper", g.adv(v("lift", r("book")), "down"), r("ladder")), qa=[
            claim("retrieve", "how", "How did they get the whale book down?", "Ms Alvarez used a ladder. She lifted the whale book down.", "helper", "book", "ladder")])
    if f.kind == "checkout":
        return scene(s("helper", v("give", r("friend"), r("book"))))
    if f.kind == "ending":
        return scene(g.join(s("friend", v("open", r("book"))), s(g.both(r("hero"), r("friend")), g.adv(v("read"), "together"))), qa=[
            claim("ending", "what_next", "What did Mina and Jun do at the end?", "Jun opened the whale book. Mina and Jun read together.", "hero", "friend", "book")])
    return None


def pottery(w, f, g):
    n, r, v, s, pp = g.n, g.ref, g.v, g.s, g.pp
    cup = r("cup")
    if f.kind == "need":
        return None  # The following goal scene states the grip problem and its consequence together.
    if f.kind == "goal":
        return scene(g.line("hero", g.me(v("want", v("give", r("grandpa"), n("cup", det="a")))), listener="helper"),
                     g.join(s(g.possess(cup, g.cn("handle")), g.be("wide")),
                            s(g.possess(r("grandpa"), g.cn("hand")), g.be("stiff")), "because"), qa=[
            claim("gift", "who", "Who was Bea making the cup for?", "Bea wanted to give the cup to Grandpa Len. Its handle was wide.", "hero", "grandpa", "cup"),
            claim("grip_reason", "why", "Why did the cup have a wide handle?", "Grandpa Len's hand was stiff. The cup had a wide handle for him.", "grandpa", "cup")])
    if f.kind == "slip":
        return scene(g.join(s(r("tool"), v("slip")), s(cup, g.be("dented"))), qa=[
            claim("accident", "what", "What happened when the shaping rib slipped?", "The shaping rib slipped. The cup was dented.", "tool", "cup")])
    if f.kind == "inspect":
        return scene(g.line("helper", s(g.possess(cup, g.cn("wall")), g.be("thick"), tense="present"), listener="hero"), qa=[
            claim("inspection", "what", "What did Mr Ivo say about the cup's wall?", "Mr Ivo said the wall was thick. He told Bea.", "helper", "hero", "cup")])
    if f.kind == "thumb":
        return scene(g.line("hero", g.me(v("want", n("thumb rest", det="a"))), listener="helper"),
                     g.using("hero", v("shape", n("thumb rest", det="a")), r("sponge")), qa=[
            claim("design", "how", "How did Bea use the dent?", "Bea shaped a thumb rest. She used the sponge.", "hero", "cup", "sponge")])
    if f.kind == "smooth":
        return scene(g.line("hero", g.me(v("want", v("smooth", n("dent")))), listener="helper"),
                     g.using("hero", v("smooth", n("dent")), r("sponge")), qa=[
            claim("design", "how", "How did Bea change the dent?", "Bea smoothed the dent. She used the sponge.", "hero", "cup", "sponge")])
    if f.kind == "deliver":
        assert {"fired", "cool", "glazed"} <= w.entities["cup"].state
        # The two firings and glaze are all completed trace events, not predicted effects.
        assert {"bisque", "glaze", "fire"} <= {x["frame"]["kind"] for x in w.history}
        return scene(s("helper", g.adv(v("fire", cup), "twice")),
                     s(cup, g.be("cool")), qa=[
            claim("firing", "who", "Who fired the cup?", "Mr Ivo fired the cup twice. The cup was cool afterward.", "helper", "cup")])
    if f.kind == "give":
        return scene(s("hero", v("give", r("grandpa"), cup)))
    if f.kind == "use":
        return scene(s("grandpa", g.adv(v("pour", n("tea", det="bare")), pp("into", cup))), qa=[
            claim("tea", "what", "What did Grandpa Len put in the cup?", "Grandpa Len poured tea into the cup. The cup held tea.", "grandpa", "cup")])
    if f.kind == "ending":
        if "thumb_design" in w.flags:
            return scene(s(g.possess(r("grandpa"), g.cn("thumb")), g.adv(v("rest"), pp("in", n("thumb rest")))), qa=[
                claim("ending", "where", "Where did Grandpa Len rest his thumb?", "His thumb rested in the thumb rest. He used the shape Bea had made.", "grandpa", "cup")])
        return scene(s("grandpa", v("hold", g.possess(cup, g.cn("handle", "wide")))), qa=[
            claim("ending", "what_next", "How did Grandpa Len hold the cup at the end?", "Grandpa Len held its wide handle. The handle gave him a place to grip.", "grandpa", "cup")])
    return None
