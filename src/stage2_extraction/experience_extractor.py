"""
Work Experience and Project Experience Extraction Engine.
Robustly identifies jobs, internships, research roles, date periods,
achievement bullet points, and project portfolios across diverse resume formats.
"""
import re
from typing import List, Dict, Any, Optional
from src.utils.text_helpers import clean_bullet_points

ACTION_VERBS = {
    'developed', 'built', 'created', 'implemented', 'designed', 'engineered',
    'maintained', 'utilized', 'achieved', 'analyzed', 'automated', 'configured',
    'tested', 'deployed', 'collaborated', 'led', 'managed', 'integrated',
    'trained', 'evaluated', 'spearheaded', 'optimized', 'resolved', 'architected',
    'presented', 'fine-tuned', 'packaged', 'served', 'conducted', 'authored',
    'facilitated', 'assisted', 'generated', 'streamlined', 'delivered', 'formulated',
    'mentored', 'researched', 'executed', 'programmed', 'constructed', 'established'
}

DATE_REGEX = re.compile(
    r'(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}|\d{1,2}[\/\-]\d{4}|\d{4})\s*[-–—to\s]+\s*(?:Present|Current|Ongoing|Till\s*Date|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}|\d{1,2}[\/\-]\d{4}|\d{4})|\d{1,2}\s*(?:Months?|Weeks?|Years?)',
    re.IGNORECASE
)

ROLE_PATTERNS = [
    r'(?:Senior|Junior|Lead|Chief|Principal|Associate|Staff|Head|Assistant|Trainee|Graduate|Summer|Virtual|Winter)?\s*'
    r'(?:Software|Full\s*Stack|Front\s*end|Back\s*end|Web|Mobile|iOS|Android|Cloud|DevOps|Platform|Data|Database|ML|AI|Machine\s*Learning|Deep\s*Learning|Data\s*Science|Computer\s*Vision|NLP|QA|Test|Automation|Security|Cybersecurity|Systems?|Network|Embedded|Firmware|IT)?\s*'
    r'(?:Engineer|Developer|Programmer|Architect|Designer|Analyst|Consultant|Scientist|Specialist|Administrator|Officer|Coordinator|Manager|Lead|Intern(?:ship)?|Trainee|Apprentice|Associate|Fellow|Practitioner|Researcher|Instructor|Assistant)',
    r'Intern(?:ship)?',
    r'Trainee',
    r'Apprentice',
    r'Teaching\s*Assistant',
    r'Research\s*Assistant'
]

EXPERIENCE_HEADERS = [
    r'(?:WORK|PROFESSIONAL|EMPLOYMENT|RELEVANT|INDUSTRY|CAREER)?\s*EXPERIENCE',
    r'EMPLOYMENT\s*(?:HISTORY|RECORD)?',
    r'WORK\s*HISTORY',
    r'INTERNSHIPS?',
    r'INTERNSHIP\s*EXPERIENCE',
    r'SUMMER\s*INTERNSHIPS?',
    r'VIRTUAL\s*INTERNSHIPS?',
    r'INDUSTRIAL\s*TRAINING',
    r'TRAINING\s*(?:&|AND)?\s*INTERNSHIPS?',
    r'EXPERIENCE\s*(?:&|AND|\/)\s*INTERNSHIPS?',
    r'INTERNSHIPS?\s*(?:&|AND|\/)\s*EXPERIENCE',
    r'EXPERIENCE\s*(?:&|AND|\/)\s*PROJECTS',
    r'PROFESSIONAL\s*BACKGROUND',
    r'PRACTICUM',
    r'APPRENTICESHIPS?'
]

PROJECT_HEADERS = [
    r'(?:ACADEMIC|TECHNICAL|PERSONAL|KEY|MAJOR|MINI|CAPSTONE|SIGNIFICANT|SELECTED|NOTABLE|SOFTWARE|ENGINEERING|COURSE|LIVE)?\s*PROJECTS?',
    r'PROJECT\s*(?:WORK|DETAILS|EXPERIENCE|PORTFOLIO|UNDERTAKEN)',
    r'SYSTEM\s*(?:IMPLEMENTATIONS?|DEVELOPMENTS?)'
]

OTHER_HEADERS = [
    r'EDUCATION', r'ACADEMIC\s+BACKGROUND', r'QUALIFICATIONS?',
    r'SKILLS', r'TECHNICAL\s+SKILLS', r'CORE\s+COMPETENCIES', r'TOOLS\s*(?:&|AND)?\s*TECHNOLOGIES',
    r'CERTIFICATIONS?', r'LICENSES?', r'COURSES?',
    r'AWARDS?', r'HONORS?', r'ACHIEVEMENTS?', r'ACCOMPLISHMENTS?',
    r'PUBLICATIONS?', r'PAPERS?',
    r'LANGUAGES?', r'VOLUNTEER(?:ING)?', r'INTERESTS?', r'HOBBIES',
    r'DECLARATION', r'PERSONAL\s+DETAILS', r'REFERENCES?', r'STRENGTHS', r'EXTRA-CURRICULAR\s+ACTIVITIES'
]

TECH_WORDS = {
    'python', 'java', 'c++', 'c#', 'c', 'javascript', 'typescript', 'react',
    'react.js', 'reactjs', 'node', 'nodejs', 'node.js', 'angular', 'vue', 'html',
    'html5', 'css', 'css3', 'sql', 'mysql', 'postgresql', 'sqlite', 'mongodb',
    'docker', 'kubernetes', 'aws', 'gcp', 'azure', 'django', 'flask', 'fastapi',
    'streamlit', 'opencv', 'pytorch', 'tensorflow', 'keras', 'nlp', 'git',
    'github', 'linux', 'tailwind', 'bootstrap', 'sass', 'redux', 'express',
    'postman', 'pandas', 'numpy', 'scipy', 'scikit-learn', 'sklearn'
}

TECH_OR_METADATA_REGEX = re.compile(
    r'^\s*[*_#•\-\–—\s]*'
    r'(?:'
    r'technolog(?:y|ies)(?:\s*(?:\/|&|and)\s*tools?)?(?:\s*used)?|'
    r'tools?(?:\s*(?:\/|&|and)\s*technolog(?:y|ies))?(?:\s*used)?|'
    r'tech\s*stack|technology\s*stack|technical\s*stack|'
    r'environment(?:\s*(?:\/|&|and)\s*tools?)?|'
    r'frameworks?(?:\s*used)?|libraries(?:\s*used)?|'
    r'skills?\s*(?:used)?|languages?\s*(?:used)?|'
    r'built\s*with|tools\s*used|technologies\s*used|'
    r'hardware(?:\s*(?:\/|&|and)\s*software)?|'
    r'software(?:\s*(?:\/|&|and)\s*hardware)?|'
    r'key\s*(?:technologies|tools|features|highlights|responsibilities)|'
    r'(?:project\s*)?(?:description|overview|details|summary|scope|objective|features|responsibilities|role)|'
    r'domain(?:\s*name)?|client(?:\s*name)?|duration(?:\s*period)?|team\s*size'
    r')\s*[:\-–—\.]*',
    re.IGNORECASE
)


class ExperienceExtractor:
    """Extracts employment history, internships, and project achievements from resume text."""

    def extract_experience(self, text: str) -> Dict[str, Any]:
        """Extract structured work experiences and projects."""
        exp_lines, proj_lines = self._extract_sections(text)

        work_items = self._parse_work_blocks(exp_lines)
        proj_items = self._parse_project_blocks(proj_lines)

        # Fallback to whole-text heuristic if sections weren't explicitly captured
        if not work_items:
            work_items = self._fallback_work_scan(text)
        if not proj_items:
            proj_items = self._fallback_project_scan(text)

        raw_exp_text = "\n".join(exp_lines)
        raw_proj_text = "\n".join(proj_lines)

        return {
            "work_experience": work_items,
            "projects": proj_items,
            "raw_experience_text": raw_exp_text,
            "raw_projects_text": raw_proj_text
        }

    def _is_header_line(self, line: str, patterns: List[str]) -> bool:
        clean = line.strip().strip('*#_•-–—:[]()|')
        if not clean or len(clean) > 55:
            return False
        for pat in patterns:
            if re.fullmatch(rf'(?i){pat}', clean) or re.match(rf'(?i)^{pat}\s*[:\-–—]?$', clean):
                return True
        return False

    def _extract_sections(self, text: str) -> (List[str], List[str]):
        """Isolate experience and project lines across all section occurrences."""
        exp_lines: List[str] = []
        proj_lines: List[str] = []
        cur_type: Optional[str] = None

        for line in text.splitlines():
            l_str = line.strip()
            if not l_str:
                continue

            if self._is_header_line(l_str, EXPERIENCE_HEADERS):
                cur_type = 'exp'
                continue
            elif self._is_header_line(l_str, PROJECT_HEADERS):
                cur_type = 'proj'
                continue
            elif self._is_header_line(l_str, OTHER_HEADERS):
                cur_type = 'other'
                continue

            if cur_type == 'exp':
                exp_lines.append(l_str)
            elif cur_type == 'proj':
                proj_lines.append(l_str)

        return exp_lines, proj_lines

    def _clean_company_name(self, comp: str) -> str:
        """Clean extracted organization or company name. Returns empty string if none found."""
        if not comp:
            return ""
        comp = re.sub(r'^\s*(?:Company(?:\s*Name)?|Organization|Employer|Firm|At)\s*[:\-–\s]*', '', comp, flags=re.I)
        comp = re.sub(r'^\s*\d+[\.\)]\s*', '', comp)
        comp = re.sub(r'^[•\-\*\>]\s*', '', comp)
        comp = comp.strip('*_#•-–—:[]()| ')
        return comp  # empty string means unknown; UI skips rendering

    def _clean_role_name(self, role: str) -> str:
        """Clean extracted position or internship title."""
        if not role:
            return "Software Professional / Intern"
        role = re.sub(r'^\s*(?:Role|Position|Title|Designation|Job\s*Title)\s*[:\-–\s]*', '', role, flags=re.I)
        role = re.sub(r'^\s*\d+[\.\)]\s*', '', role)
        role = re.sub(r'^[•\-\*\>]\s*', '', role)
        role = role.strip('*_#•-–—:[]()| ')
        return role or "Software Professional / Intern"

    def _parse_work_blocks(self, lines: List[str]) -> List[Dict[str, Any]]:
        """Parse separate positions/internships with title, organization, dates, and bullets."""
        if not lines:
            return []

        entries: List[Dict[str, Any]] = []
        curr: Optional[Dict[str, Any]] = None

        for line in lines:
            line_clean = line.strip()
            if not line_clean:
                continue

            raw = re.sub(r'^[•\-\*\>]\s*', '', line_clean).strip()
            first_w = raw.split()[0].lower().strip(',.:;') if raw.split() else ''
            is_bullet = line_clean.startswith(('•', '-', '*', '>', '–')) or first_w in ACTION_VERBS

            # Check for labeled lines
            comp_m = re.match(r'^(?:Company(?:\s*Name)?|Organization|Employer|Firm)\s*[:\-–]\s*(.+)', line_clean, re.I)
            role_m = re.match(r'^(?:Role|Position|Title|Designation|Job\s*Title)\s*[:\-–]\s*(.+)', line_clean, re.I)
            date_m = re.match(r'^(?:Duration|Period|Dates?|Tenure)\s*[:\-–]\s*(.+)', line_clean, re.I)
            num_m = re.match(r'^\s*(\d+)[\.\)]\s*(.+)', line_clean)

            # Check for date patterns
            d_find = DATE_REGEX.search(line_clean)
            date_val = d_find.group(0) if d_find else None

            # Check for role keywords
            has_role = any(re.search(rf'\b{p}\b', line_clean, re.I) for p in ROLE_PATTERNS) and not is_bullet

            # Decide whether to start a new position entry
            start_new = False
            if not curr:
                start_new = True
            elif num_m:
                start_new = True
            elif (comp_m or role_m or has_role) and (curr.get('raw_bullets') or (curr.get('title') != 'Software Professional / Intern' and not curr.get('company'))):
                start_new = True

            if start_new:
                if curr:
                    curr['bullets'] = clean_bullet_points(curr['raw_bullets'])
                    entries.append(curr)

                curr = {
                    'title': 'Software Professional / Intern',
                    'company': '',
                    'dates': 'Dates Not Specified',
                    'raw_bullets': []
                }

            # Extract fields into current entry
            if comp_m:
                curr['company'] = self._clean_company_name(comp_m.group(1))
            elif role_m:
                curr['title'] = self._clean_role_name(role_m.group(1))
            elif date_m:
                curr['dates'] = date_m.group(1).strip()
            elif is_bullet:
                curr['raw_bullets'].append(line_clean)
            else:
                clean_no_date = DATE_REGEX.sub('', line_clean).strip(' |–-,()[]')
                if date_val and curr['dates'] == 'Dates Not Specified':
                    curr['dates'] = date_val

                # Check if compound line with delimiter
                if ' at ' in clean_no_date or ' @ ' in clean_no_date:
                    parts = re.split(r'\s+(?:at|@)\s+', clean_no_date, flags=re.I)
                    curr['title'] = self._clean_role_name(parts[0])
                    if len(parts) > 1 and not curr.get('company'):
                        curr['company'] = self._clean_company_name(parts[1])
                elif '|' in clean_no_date or ' - ' in clean_no_date or ' – ' in clean_no_date or ',' in clean_no_date or ' -- ' in clean_no_date:
                    parts = re.split(r'\s*\|\s*|\s+[-–—]\s+|\s*--\s*|\s*,\s*', clean_no_date)
                    for part in parts:
                        p_s = part.strip()
                        if any(re.search(rf'\b{p}\b', p_s, re.I) for p in ROLE_PATTERNS):
                            curr['title'] = self._clean_role_name(p_s)
                        elif len(p_s) >= 2 and not curr.get('company'):
                            curr['company'] = self._clean_company_name(p_s)
                elif has_role:
                    curr['title'] = self._clean_role_name(clean_no_date)
                elif not curr.get('company') and 2 <= len(clean_no_date) <= 60 and not clean_no_date.endswith('.'):
                    curr['company'] = self._clean_company_name(clean_no_date)

        if curr:
            curr['bullets'] = clean_bullet_points(curr['raw_bullets'])
            entries.append(curr)

        return entries

    def _is_pure_tech_line(self, line: str) -> bool:
        """Check if line is merely a comma-separated list of programming languages/tools."""
        tokens = [t.strip().lower() for t in re.split(r'[,|/–\-]+', line) if t.strip()]
        if not tokens:
            return False
        hits = sum(1 for t in tokens if t in TECH_WORDS)
        return (hits / len(tokens)) >= 0.5

    def _clean_project_name(self, name: str) -> str:
        """Strip leading numbering, bullets, suffixes, and parenthetical tech/dates from project title."""
        name = re.sub(r'^[•\-\*\>]\s*', '', name.strip())
        name = re.sub(r'^\s*(?:Project(?:\s*(?:Name|Title))?\s*\d*[:\-–\s]*|\d+[\.\)]\s*)+', '', name, flags=re.I)
        name = re.sub(r'\s*\([^)]*\).*$', '', name)
        if '|' in name or ' - ' in name or ' – ' in name or ' -- ' in name:
            parts = re.split(r'\s*\|\s*|\s+[-–—]\s+|\s*--\s*', name)
            if parts and parts[0].strip():
                name = parts[0].strip()
        if ':' in name:
            parts = name.split(':', 1)
            if 3 <= len(parts[0].strip()) <= 55:
                name = parts[0].strip()
        cleaned = name.strip('*_#•-–—:[]()| ')
        # Reject if cleaned name is a known metadata/tech label
        if TECH_OR_METADATA_REGEX.match(cleaned) or self._is_pure_tech_line(cleaned):
            return ""
        return cleaned

    def _parse_project_blocks(self, lines: List[str]) -> List[Dict[str, Any]]:
        """Parse all individual projects with clean project names across all resume styles."""
        if not lines:
            return []

        projects: List[Dict[str, Any]] = []
        seen_names = set()
        curr: Optional[Dict[str, Any]] = None

        for line in lines:
            line_clean = line.strip()
            if not line_clean:
                continue

            raw = re.sub(r'^[•\-\*\>]\s*', '', line_clean).strip()
            first_w = raw.split()[0].lower().strip(',.:;') if raw.split() else ''

            # Never a project title if starting with an action verb
            if first_w in ACTION_VERBS:
                if curr:
                    curr['raw_bullets'].append(line_clean)
                continue

            # Check if delimited title (e.g., "Search Engine | Python, React")
            has_delim = bool(re.search(r'\s*\|\s*|\s+[-–—]\s+|\s*--\s*', raw))
            m_paren = re.search(r'^(.*?)\s*\(([A-Za-z0-9\s,./#+-]+)\)$', raw)
            num_m = re.match(r'^\s*(?:\d+[\.\)]|Project\s+\d+[:\-–]?|Project\s*:\s*)(.+)', line_clean, re.I)
            label_m = re.match(r'^(?:Project(?:\s*(?:Name|Title))?|Title)\s*[:\-–]\s*(.+)', line_clean, re.I)
            is_bullet_col = line_clean.startswith(('•', '-', '*', '>', '–')) and ':' in raw

            # Never a project title if it is a standalone tech/tools/metadata label without a project title
            if not (has_delim or m_paren or num_m or label_m) and (TECH_OR_METADATA_REGEX.match(raw) or self._is_pure_tech_line(raw)):
                if curr:
                    tech_val = TECH_OR_METADATA_REGEX.sub('', raw).strip(' :–-')
                    if tech_val:
                        curr['tech_stack'] = tech_val
                    elif self._is_pure_tech_line(raw):
                        curr['tech_stack'] = raw
                continue

            # Never a project title if starting with descriptive articles/prepositions
            if first_w in {'the', 'this', 'a', 'an', 'in', 'for', 'to', 'with', 'using', 'features', 'description', 'key', 'overview'}:
                if curr:
                    curr['raw_bullets'].append(line_clean)
                continue

            is_title = False
            raw_title = ''
            extracted_tech = ''

            if num_m:
                is_title = True
                raw_title = num_m.group(1).strip()
            elif label_m:
                is_title = True
                raw_title = label_m.group(1).strip()
            elif has_delim:
                parts = re.split(r'\s*\|\s*|\s+[-–—]\s+|\s*--\s*', raw)
                if parts and 3 <= len(parts[0]) <= 70 and parts[0].split()[0].lower() not in ACTION_VERBS:
                    is_title = True
                    raw_title = parts[0].strip()
                    if len(parts) > 1:
                        extracted_tech = " | ".join(parts[1:]).strip()
            elif m_paren and len(raw) <= 85:
                is_title = True
                raw_title = m_paren.group(1).strip()
                extracted_tech = m_paren.group(2).strip()
            elif is_bullet_col:
                col_parts = raw.split(':', 1)
                if 3 <= len(col_parts[0].strip()) <= 55 and col_parts[0].split()[0].lower() not in ACTION_VERBS:
                    is_title = True
                    raw_title = col_parts[0].strip()
            elif not line_clean.startswith(('•', '-', '*', '>', '–')):
                # Standalone un-bulleted line that is capitalized and doesn't end with period
                if 3 <= len(raw) <= 65 and not raw.endswith('.'):
                    if any(c.isupper() for c in raw):
                        is_title = True
                        raw_title = raw

            if is_title:
                clean_name = self._clean_project_name(raw_title)
                name_key = clean_name.lower()
                if clean_name and len(clean_name) >= 3 and name_key not in seen_names:
                    seen_names.add(name_key)
                    if curr:
                        curr['bullets'] = clean_bullet_points(curr['raw_bullets'])
                        projects.append(curr)

                    curr = {
                        'name': clean_name,
                        'tech_stack': extracted_tech,
                        'raw_bullets': [],
                        'bullets': []
                    }
            elif curr:
                if len(line_clean) > 15:
                    curr['raw_bullets'].append(line_clean)

        if curr:
            curr['bullets'] = clean_bullet_points(curr['raw_bullets'])
            projects.append(curr)

        return projects

    def _fallback_work_scan(self, text: str) -> List[Dict[str, Any]]:
        """Fallback to identify work/internship occurrences anywhere in text."""
        entries = []
        for line in text.splitlines():
            line_clean = line.strip()
            if any(re.search(rf'\b{p}\b', line_clean, re.I) for p in ROLE_PATTERNS):
                d_m = DATE_REGEX.search(line_clean)
                # Strip date from the line to get the role + company part
                clean_no_date = DATE_REGEX.sub('', line_clean).strip(' |–-,')
                if 4 <= len(clean_no_date) <= 80 and not line_clean.startswith(('•', '-', '*')):
                    # Try to split "Role | Company" or "Role at Company"
                    company = ""
                    title = clean_no_date
                    if ' at ' in clean_no_date or ' @ ' in clean_no_date:
                        parts = re.split(r'\s+(?:at|@)\s+', clean_no_date, flags=re.I)
                        title = self._clean_role_name(parts[0])
                        if len(parts) > 1:
                            company = self._clean_company_name(parts[1])
                    elif '|' in clean_no_date or ' – ' in clean_no_date or ' - ' in clean_no_date:
                        parts = re.split(r'\s*\|\s*|\s+[-–—]\s+', clean_no_date)
                        for part in parts:
                            p_s = part.strip()
                            if any(re.search(rf'\b{p}\b', p_s, re.I) for p in ROLE_PATTERNS):
                                title = self._clean_role_name(p_s)
                            elif len(p_s) >= 2 and not company:
                                company = self._clean_company_name(p_s)
                    else:
                        title = self._clean_role_name(clean_no_date)
                    entries.append({
                        "title": title,
                        "company": company,  # empty string means unknown — UI will skip rendering it
                        "dates": d_m.group(0) if d_m else "Dates Not Specified",
                        "bullets": []
                    })
        return entries[:3]

    def _fallback_project_scan(self, text: str) -> List[Dict[str, Any]]:
        """Fallback to scan for project indicators across entire text."""
        projects = []
        seen = set()
        for line in text.splitlines():
            line_clean = line.strip()
            num_match = re.match(r'^\s*(?:\d+[\.\)]|Project\s+\d+[:\-–]?|Project\s*:\s*)(.+)', line_clean, re.I)
            if num_match:
                name = num_match.group(1).strip('•-*#: ')
                if 3 <= len(name) <= 70 and name.lower() not in seen:
                    if not any(name.upper().startswith(h) for h in ["PROJECTS", "EXPERIENCE", "EDUCATION", "SKILLS"]):
                        seen.add(name.lower())
                        projects.append({
                            "name": name,
                            "tech_stack": "",
                            "bullets": []
                        })
        return projects[:4]
