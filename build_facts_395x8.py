#!/usr/bin/env python3
"""Build facts_395x8.json with 8 full-sentence facts per topic."""

import csv
import json
import re
from pathlib import Path

CSV_PATH = Path("/workspace/facts-or-whacks-395-videos.csv")
ORIGINAL_30_CSV = Path("/workspace/facts-or-whacks-30-videos.csv")
OUTPUT_JSON = Path("/workspace/facts_395x8.json")
GENERATE_SCRIPT = Path("/workspace/generate_395_facts.py")

APARTHEID_30 = [
    "Apartheid was South Africa's legal system of racial segregation (1948-1994).",
    "Nelson Mandela spent 27 years in prison for anti-apartheid activism.",
    "International boycotts and sanctions pressured the white minority government.",
    "Mandela was released in 1990 and negotiated a peaceful transition.",
    "First democratic elections held April 27, 1994 — Mandela became president.",
    "At age 75, he chose reconciliation over revenge.",
    "The Truth and Reconciliation Commission addressed past atrocities.",
    "South Africa's transition is studied as a model of peaceful revolution.",
]

EXTRA_1_29 = {
    1: [
        "The Enlightenment peaked in 18th-century Europe and reshaped governments on both sides of the Atlantic.",
        "Salons and coffeehouses spread radical new ideas about liberty, science, and human rights.",
        "Enlightenment thinkers challenged absolute monarchy and helped inspire modern constitutional democracy.",
    ],
    2: [
        "Taxation without representation became the colonists' rallying cry against British rule.",
        "The war lasted from 1775 to 1783 and forged a new republic built on Enlightenment ideals.",
        "The Treaty of Paris in 1783 formally recognized American independence from Britain.",
    ],
    3: [
        "The revolution began when commoners stormed the Bastille prison on July 14, 1789.",
        "King Louis XVI was executed by guillotine in 1793, ending over a thousand years of French monarchy.",
        "The Reign of Terror saw thousands executed before Napoleon eventually seized power.",
    ],
    4: [
        "Napoleon crowned himself Emperor of France in 1804, crowning a meteoric rise from artillery officer.",
        "His Napoleonic Code still influences legal systems across Europe and Latin America today.",
        "Defeated at Waterloo in 1815, he was exiled to Saint Helena where he died in 1821.",
    ],
    5: [
        "Toussaint Louverture led enslaved people in a revolt that defeated French, British, and Spanish forces.",
        "Haiti declared independence on January 1, 1804, becoming the first Black republic in the world.",
        "France later demanded crippling reparations that kept Haiti in debt for generations.",
    ],
    6: [
        "The Industrial Revolution began in Britain around 1760 and spread across Europe and North America.",
        "Factory work drew millions from farms into crowded cities, transforming society forever.",
        "Mechanization created vast wealth but also deep inequality and harsh working conditions.",
    ],
    7: [
        "President Thomas Jefferson commissioned the expedition to explore the newly acquired Louisiana Territory.",
        "The Corps of Discovery traveled roughly 8,000 miles from St. Louis to the Pacific and back.",
        "Their maps and journals opened the American West to settlement and trade.",
    ],
    8: [
        "Frederick Douglass escaped slavery and became one of America's greatest orators and writers.",
        "Harriet Tubman's Underground Railroad helped more than 70 enslaved people reach freedom.",
        "The movement combined moral persuasion, legal action, and direct resistance to end slavery.",
    ],
    9: [
        "James Marshall discovered gold at Sutter's Mill in January 1848, sparking a global rush.",
        "San Francisco grew from about 200 residents to 36,000 in just a few years.",
        "Most prospectors earned little while merchants and suppliers became the real winners.",
    ],
    10: [
        "Darwin spent five years aboard HMS Beagle collecting specimens across South America and the Pacific.",
        "He waited over 20 years to publish, fearing backlash against his evolutionary theory.",
        "On the Origin of Species, published in 1859, became the foundation of modern biology.",
    ],
    11: [
        "The war began when Confederate forces fired on Fort Sumter in April 1861.",
        "An estimated 620,000 soldiers died, making it America's deadliest conflict at the time.",
        "The Union victory in 1865 ended slavery and preserved the United States as one nation.",
    ],
    12: [
        "The Central Pacific and Union Pacific railroads met at Promontory Summit, Utah, on May 10, 1869.",
        "More than 20,000 Chinese laborers built the treacherous western half through mountains and desert.",
        "The railroad cut cross-country travel from months to about seven days.",
    ],
    13: [
        "The Meiji Restoration began in 1868, ending over 250 years of Tokugawa shogunate rule.",
        "Japan rapidly adopted Western industry, military methods, and education to avoid colonization.",
        "Within decades Japan defeated China and Russia, proving its transformation to the world.",
    ],
    14: [
        "Jack the Ripper killed at least five women in London's East End during the autumn of 1888.",
        "The killer taunted police and newspapers with letters signed 'Jack the Ripper.'",
        "Despite massive investigation, no suspect was ever convicted and the case remains unsolved.",
    ],
    15: [
        "Orville and Wilbur Wright ran a bicycle shop in Dayton, Ohio, before teaching themselves aerodynamics.",
        "Their Flyer achieved the first powered, controlled flight on December 17, 1903, at Kitty Hawk.",
        "Their three-axis control system remains fundamental to every aircraft flying today.",
    ],
    16: [
        "The Titanic struck an iceberg on April 14, 1912, and sank in roughly three hours.",
        "Of the 2,240 passengers and crew aboard, more than 1,500 lost their lives in the icy Atlantic.",
        "The disaster led to major reforms in maritime safety, including mandatory lifeboats for all.",
    ],
    17: [
        "Archduke Franz Ferdinand's assassination in Sarajevo on June 28, 1914, triggered the war.",
        "Trench warfare, poison gas, and machine guns made the Western Front a hellish stalemate.",
        "The Armistice on November 11, 1918, ended fighting but left a broken Europe ripe for future conflict.",
    ],
    18: [
        "Two revolutions in 1917 overthrew the tsar and brought the Bolsheviks to power under Lenin.",
        "The Romanov family was executed in 1918, ending centuries of imperial Russian rule.",
        "The USSR formed in 1922 and became a global superpower that shaped the 20th century.",
    ],
    19: [
        "The 19th Amendment granted American women the right to vote in 1920.",
        "Prohibition from 1920 to 1933 banned alcohol and fueled a booming underground speakeasy culture.",
        "The stock market crash of October 1929 ended the decade and ushered in the Great Depression.",
    ],
    20: [
        "Alexander Fleming discovered penicillin by accident in 1928 when mold contaminated a petri dish.",
        "Scientists Florey and Chain later developed methods to mass-produce the antibiotic for WWII.",
        "Penicillin launched the antibiotic era and saved countless lives from bacterial infections.",
    ],
    21: [
        "Black Tuesday on October 29, 1929, saw the stock market lose billions in a single day.",
        "Unemployment in the United States eventually reached roughly 25 percent.",
        "Franklin Roosevelt's New Deal programs provided relief, recovery, and lasting reforms like Social Security.",
    ],
    22: [
        "World War II killed an estimated 70 to 85 million people, the deadliest conflict in human history.",
        "The Holocaust systematically murdered six million Jews and millions of other victims.",
        "Allied victory in 1945 reshaped the global order and ushered in the nuclear age.",
    ],
    23: [
        "Allied forces landed on five Normandy beaches on June 6, 1944, in the largest amphibious invasion ever.",
        "Omaha Beach saw the heaviest American casualties of the entire operation.",
        "D-Day opened the Western Front and began the liberation of Nazi-occupied Europe.",
    ],
    24: [
        "Nazi death camps like Auschwitz, Treblinka, and Sobibor were built for industrial-scale murder.",
        "The Wannsee Conference in 1942 coordinated the 'Final Solution' to exterminate European Jews.",
        "Allied liberation of the camps in 1945 revealed horrors that led to the promise of 'Never again.'",
    ],
    25: [
        "Mahatma Gandhi led India to independence through nonviolent civil disobedience and mass protest.",
        "India gained independence on August 15, 1947, but was simultaneously partitioned into India and Pakistan.",
        "The partition displaced 10 to 20 million people and killed an estimated 1 to 2 million.",
    ],
    26: [
        "The Soviet Union launched Sputnik in 1957, shocking the West and starting the Space Race.",
        "Yuri Gagarin became the first human in space in 1961, and Neil Armstrong walked the Moon in 1969.",
        "The Cold War rivalry also drove advances in satellites, computing, and nuclear technology.",
    ],
    27: [
        "Rosa Parks refused to give up her bus seat in Montgomery, Alabama, on December 1, 1955.",
        "Martin Luther King Jr. delivered his 'I Have a Dream' speech at the March on Washington in 1963.",
        "The Civil Rights Act of 1964 and Voting Rights Act of 1965 dismantled legal segregation.",
    ],
    28: [
        "East Germany built the Berlin Wall in 1961 to stop citizens from fleeing to the West.",
        "Ronald Reagan famously demanded in 1987: 'Mr. Gorbachev, tear down this wall!'",
        "On November 9, 1989, crowds surged through opened gates and began tearing the wall apart.",
    ],
    29: [
        "ARPANET, the military precursor to the internet, sent its first message in 1969.",
        "Tim Berners-Lee invented the World Wide Web at CERN in 1989, making the internet accessible to all.",
        "Today more than five billion people around the world are connected online.",
    ],
}


def load_new_topics():
    ns = {}
    src = GENERATE_SCRIPT.read_text(encoding="utf-8")
    exec(compile(src.split("def read_existing_rows")[0], str(GENERATE_SCRIPT), "exec"), ns)
    return ns["NEW_TOPICS"]


def load_extra_31_395():
    extra_path = Path("/workspace/extra_facts_31_395.json")
    if extra_path.exists():
        data = json.loads(extra_path.read_text(encoding="utf-8"))
        return {int(k): v for k, v in data.items()}
    return {}


def expand_fact(fact: str, title: str = "") -> str:
    """Expand a short bullet into a full prose sentence."""
    raw = fact.strip()
    f = raw.rstrip(".")
    if not f:
        return f
    f_key = f
    f = f[0].upper() + f[1:]

    replacements = {
        "Voltaire Locke & Rousseau challenged kings": (
            "Voltaire, Locke, and Rousseau challenged the authority of kings and churches across Europe"
        ),
        "Encyclopedie cataloged all knowledge": (
            "The Encyclopédie cataloged human knowledge and spread Enlightenment ideas to a wide audience"
        ),
        "Reason over superstition": (
            "Enlightenment thinkers placed reason above superstition in politics, science, and daily life"
        ),
        "Inspired revolutions worldwide": (
            "Enlightenment ideals inspired revolutions in America, France, and beyond"
        ),
        "Free speech. Tolerance. Rights": (
            "Enlightenment philosophers championed free speech, religious tolerance, and individual rights"
        ),
        "Mount Vesuvius erupted August 79 CE": (
            "Mount Vesuvius erupted in August 79 CE, burying the Roman city of Pompeii"
        ),
        "Ash preserved bodies buildings and graffiti": (
            "Volcanic ash preserved bodies, buildings, and graffiti in extraordinary detail"
        ),
        "Pliny the Younger witnessed and recorded it": (
            "Pliny the Younger witnessed the eruption and left a vivid written account"
        ),
        "Rediscovered 1748 frozen in time": (
            "Pompeii was rediscovered in 1748, frozen in time beneath the ash"
        ),
    }
    if f_key in replacements:
        f = replacements[f_key]

    words = f.split()
    if len(words) < 8 and "— a key part of the story" not in f:
        if title and title.lower() not in f.lower() and f_key not in replacements:
            f = f"{f} — a key part of the story of {title}"

    if not f.endswith("."):
        f += "."
    return f


def load_original_30_bullets() -> dict[int, list[str]]:
    bullets_by_num = {}
    with ORIGINAL_30_CSV.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            num = int(row["topic_number"])
            bullets = [b.strip() for b in row["on_screen_bullets"].split("|") if b.strip()]
            bullets_by_num[num] = bullets
    return bullets_by_num


def get_base_facts(num: int, row: dict, new_topics: list, original_30: dict) -> list[str]:
    if num == 30:
        return list(APARTHEID_30)
    if num <= 29:
        bullets = original_30.get(num, [])
        if not bullets:
            bullets = [b.strip() for b in row["on_screen_bullets"].split("|") if b.strip()][:5]
        return [expand_fact(b, row["title"]) for b in bullets[:5]]
    topic = new_topics[num - 31]
    return [expand_fact(f, topic["title"]) for f in topic["facts"]]


def get_extra_facts(num: int, extra_31_395: dict) -> list[str]:
    if num == 30:
        return []
    if num in EXTRA_1_29:
        return EXTRA_1_29[num]
    return extra_31_395.get(num, [])


def build_entry(num: int, title: str, row: dict, new_topics: list, extra_31_395: dict, original_30: dict) -> dict:
    base = get_base_facts(num, row, new_topics, original_30)
    if num == 30:
        facts = base
    else:
        extras = get_extra_facts(num, extra_31_395)
        if len(extras) < 3:
            raise ValueError(f"Topic {num} ({title}) needs 3 extra facts, got {len(extras)}")
        facts = base[:5] + extras[:3]
    if len(facts) != 8:
        raise ValueError(f"Topic {num} ({title}) has {len(facts)} facts, expected 8")
    return {"topic_number": num, "title": title, "facts": facts}


def main():
    new_topics = load_new_topics()
    extra_31_395 = load_extra_31_395()
    original_30 = load_original_30_bullets()
    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if len(rows) != 395:
        raise SystemExit(f"Expected 395 CSV rows, got {len(rows)}")
    entries = []
    for row in rows:
        num = int(row["topic_number"])
        entry = build_entry(num, row["title"], row, new_topics, extra_31_395, original_30)
        entries.append(entry)
    OUTPUT_JSON.write_text(json.dumps(entries, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(entries)} topics to {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
