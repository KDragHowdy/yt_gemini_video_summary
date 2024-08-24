import os
from report_generator import (
    generate_markdown_report,
    generate_structured_slides_appendix,
    format_intertextual_references,
)


def generate_and_save_reports(
    video_id,
    video_title,
    summary_chunks,
    intertextual_chunks,
    video_analyses,
    output_dir,
):
    try:
        main_report = generate_markdown_report(
            video_id,
            video_title,
            summary_chunks,
            intertextual_chunks,
            video_analyses,
        )
        structured_slides = generate_structured_slides_appendix(
            video_id, video_title, video_analyses
        )

        shortened_title = "".join(e for e in video_title if e.isalnum())[:20].lower()
        filename = f"final_report_{shortened_title}.md"

        full_report = f"{main_report}\n\n{structured_slides}\n\n"
        full_report += "# Appendix B: Intertextual References\n\n"
        full_report += format_intertextual_references(intertextual_chunks)

        report_file = os.path.join(output_dir, filename)
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(full_report)

        print(f"Final report saved to {report_file}")
        return report_file
    except Exception as e:
        print(f"Error in generate_and_save_reports: {str(e)}")
        raise
