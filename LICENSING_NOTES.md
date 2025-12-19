# Licensing Compliance Notes

## Summary

This project is primarily based on the [LangChain Documentation](https://github.com/langchain-ai/docs) (MIT License), with a smaller portion derived from [Alibaba Cloud ACP Learning](https://github.com/AlibabaCloudDocs/aliyun_acp_learning) (Apache License 2.0).

## Project License: MIT

We've chosen the **MIT License** as the primary license for this project because:
1. The majority of the code comes from LangChain docs (MIT)
2. MIT is simple, permissive, and widely compatible
3. MIT is compatible with Apache 2.0 (we can include Apache-licensed code in an MIT project)
4. It allows maximum flexibility for users

## Source Attribution

### Primary Source (≈80-90% of codebase)
**LangChain Documentation**
- Repository: https://github.com/langchain-ai/docs
- License: MIT License
- Copyright: (c) 2025 LangChain
- Content: Documentation structure, LangChain examples, LangGraph tutorials, integration patterns

### Secondary Source (≈10-20% of codebase)
**Alibaba Cloud ACP Learning**
- Repository: https://github.com/AlibabaCloudDocs/aliyun_acp_learning
- License: Apache License 2.0
- Copyright: Alibaba Cloud
- Content: Some specific examples, certain educational materials, Alibaba Cloud integration samples

## What Was Done

### 1. LICENSE File ✅
- Created `LICENSE` with MIT License text
- **ACTION REQUIRED**: Update line 3:
  - Change `Copyright (c) 2025 [Your Name/Organization]` to your actual name

### 2. NOTICE File ✅
- Created comprehensive `NOTICE` file that:
  - Credits LangChain as primary source
  - Credits Alibaba ACP as secondary source
  - Lists modifications made
  - Includes both license summaries
- **ACTION REQUIRED**: Update line 2:
  - Change `Copyright (c) 2025 [Your Name/Organization]` to your actual name

### 3. README.md ✅
- Updated with clear attribution section
- Shows primary vs secondary sources
- Links to LICENSE and NOTICE files
- Includes acknowledgments section

## License Compatibility

### ✅ MIT + Apache 2.0 = Compatible

This combination is legally sound:

**MIT License Requirements:**
- ✅ Include copyright notice
- ✅ Include license text

**Apache 2.0 Requirements (for the Alibaba portions):**
- ✅ Include copyright notice
- ✅ Provide attribution (done in NOTICE)
- ✅ State changes (done in NOTICE)
- ✅ Include copy of Apache license terms (done in NOTICE)

**Result:** MIT as the primary license is compatible with including Apache-licensed code, as long as we properly attribute and comply with Apache requirements for those specific portions.

## What You Need to Do

### Required Actions:

1. **Update Copyright Holder** (REQUIRED):
   - In `LICENSE` (line 3): Replace `[Your Name/Organization]`
   - In `NOTICE` (line 2): Replace `[Your Name/Organization]`
   
   Example:
   ```
   Copyright (c) 2025 John Doe
   # or
   Copyright (c) 2025 ABC Training Company
   ```

2. **Review Source Attribution** (Recommended):
   - Verify the percentages of code from each source
   - Update NOTICE if the distribution is significantly different
   - Add specific file attributions if needed

### Optional Actions:

3. **Add File Headers** (Optional but Professional):
   
   For files primarily from LangChain:
   ```python
   # Copyright (c) 2025 [Your Name]
   # Based on LangChain documentation (https://github.com/langchain-ai/docs)
   # Licensed under MIT License
   ```
   
   For files partially from Alibaba:
   ```python
   # Copyright (c) 2025 [Your Name]
   # Portions derived from Alibaba Cloud ACP Learning
   # (https://github.com/AlibabaCloudDocs/aliyun_acp_learning)
   # Licensed under MIT License; original portions under Apache 2.0
   ```

## License Comparison

### MIT License (Primary)

**✅ You CAN:**
- Use commercially
- Modify freely
- Distribute
- Sublicense
- Use privately

**⚠️ You MUST:**
- Include copyright notice
- Include license text

**❌ You CANNOT:**
- Hold author liable
- Expect warranty

### Apache 2.0 License (Secondary Portions)

**✅ You CAN:**
- Use commercially
- Modify freely
- Distribute
- Sublicense (with conditions)
- Use privately
- Use patent grants

**⚠️ You MUST:**
- Include copyright notice
- Include license text
- State significant changes
- Preserve NOTICE file content

**❌ You CANNOT:**
- Use trademarks without permission
- Hold author liable
- Expect warranty

## Distribution Requirements

When distributing this project (Git, npm, etc.):

✅ Include `LICENSE` file (MIT)  
✅ Include `NOTICE` file (attributions)  
✅ Keep copyright notices intact  
✅ Don't claim you wrote the original LangChain or Alibaba code  

## Best Practices

1. **When Adding New Code:**
   - If copying from LangChain docs: You're good, same license
   - If copying from Alibaba ACP: Add attribution comment
   - If copying from elsewhere: Check license compatibility

2. **When Modifying Existing Code:**
   - You can freely modify MIT-licensed code
   - For Apache 2.0 portions, note changes in comments or NOTICE

3. **When Using Dependencies:**
   - Check licenses of all packages in requirements.txt and package.json
   - Most are permissive (MIT, Apache, BSD)
   - Avoid GPL unless you're okay with copyleft

## Common Questions

**Q: Can I use this project commercially?**  
A: Yes! MIT allows commercial use.

**Q: Do I need to open source my modifications?**  
A: No, MIT doesn't require this (unlike GPL).

**Q: Can I change the license?**  
A: You can license YOUR modifications differently, but must preserve original license notices for the LangChain and Alibaba portions.

**Q: Do I need to credit LangChain and Alibaba?**  
A: Yes, keeping the NOTICE file and copyright notices is required.

**Q: What if I remove all Alibaba code?**  
A: You can simplify to just MIT and LangChain attribution (but keep records).

## References

- **LangChain Docs**: https://github.com/langchain-ai/docs (MIT)
- **Alibaba ACP**: https://github.com/AlibabaCloudDocs/aliyun_acp_learning (Apache 2.0)
- **MIT License**: https://opensource.org/licenses/MIT
- **Apache 2.0**: http://www.apache.org/licenses/LICENSE-2.0
- **License Compatibility**: https://opensource.stackexchange.com/questions/license-compatibility

## Disclaimer

This document provides general guidance but does not constitute legal advice. For specific legal questions, consult with a qualified attorney.

---

**Created**: December 17, 2025  
**Last Updated**: December 17, 2025  
**Version**: 2.0 (Corrected to reflect LangChain as primary source)
