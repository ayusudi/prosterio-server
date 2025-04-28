from typing import Dict, List, Any
import json # Import json for handling variant types if needed

# Assuming 'id' passed is the employee_id and we also need user_id
# Adjust the signature if 'id' represents user_id or if pm_email is still needed
def compile_to_chunk(data: Dict[str, Any], employee_id: int, user_id: int):
    full_name = data.get("full_name", "N/A")
    email = data.get("email", "N/A")
    job_title = data.get("job_title", "N/A")
    promotion_years = data.get("promotion_years") # Can be None or integer
    profile = data.get("profile", "")
    skills = data.get("skills", [])
    professional_experiences = data.get("professional_experiences", [])
    educations = data.get("educations", [])
    publications = data.get("publications", [])
    distinctions = data.get("distinctions", [])
    certifications = data.get("certifications", [])
    chunks = []
    def add_chunk(chunk_type: str, content: str):
        """Helper function to create and add a chunk dictionary."""
        formatted_content = content.replace("\n", ". ").strip()
        chunks.append({
            "chunk_text": f"{chunk_type.upper()} of {full_name}: {formatted_content}",
            "type": chunk_type.upper(),
            "user_id": user_id,
            "employee_id": employee_id,
        })

    # --- Create Chunks ---

    # 1. General Information Chunk
    info_content = f"Full Name: {full_name}\nEmail: {email}\nJob Title: {job_title}"
    if promotion_years is not None:
        info_content += f"\nPromotion Year(s): {promotion_years}"
    if profile:
        info_content += f"\nProfile Summary: {profile}"
    add_chunk("INFORMATION", info_content)

    # 2. Skills Chunk
    if skills:
        skills_content = ",".join(skills)
        add_chunk("SKILLS", skills_content)

    # 3. Professional Experiences Chunks
    if professional_experiences:
        for exp in professional_experiences:
            exp_content =  f"Working at {exp.get('company', 'N/A')} as {exp.get('job_title', 'N/A')} in {exp.get('location', 'N/A')}. {'. '.join(exp.get('description', []))}"
            add_chunk("PROFESSIONAL_EXPERIENCE", exp_content)

    # 4. Educations Chunks
    if educations:
        for edu in educations:
            edu_content = f"Learned {edu.get('title', 'N/A')} at {edu.get('institution', 'N/A')} from {edu.get('date_start', 'N/A')} to {edu.get('date_end', 'N/A')} with a score of {edu.get('score', 'N/A')}. {edu.get('description', '')}"
            add_chunk("EDUCATION", edu_content)

    # 5. Publications Chunks
    if publications:
        for pub in publications:
            pub_content = (f"Published in {pub.get('publication', 'N/A')} in {pub.get('date', 'N/A')}.")
            add_chunk("PUBLICATION", pub_content)

    # 6. Distinctions Chunks
    if distinctions:
        for dist in distinctions:
            dist_content = f"Notable {dist.get('name', 'N/A')}: {dist.get('description', '')}"
            add_chunk("DISTINCTION", dist_content)

    # 7. Certifications Chunk
    if certifications:
        cert_content = " | ".join(certifications)
        add_chunk("CERTIFICATIONS", cert_content)
        
    return chunks
