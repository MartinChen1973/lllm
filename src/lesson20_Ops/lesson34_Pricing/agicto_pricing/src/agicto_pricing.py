"""
Web interface for viewing and filtering Agicto model pricing data.
Reuses scraper functions from agicto_spider.py.
"""

import json
import threading
from pathlib import Path
from flask import Flask, render_template_string, jsonify
from agicto_spider import fetch_page, extract_all_models

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agicto Model Pricing</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; padding: 1rem; background: #f5f5f5; }
        .container { max-width: 1400px; margin: 0 auto; background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        .header { padding: 1rem 1.5rem; border-bottom: 1px solid #e0e0e0; display: flex; justify-content: space-between; align-items: center; }
        h1 { font-size: 1.5rem; color: #333; }
        .sponsor-info { text-align: right; font-size: 0.75rem; color: #666; line-height: 1.5; }
        .sponsor-info div { text-decoration: underline; }
        .sponsor-info a { color: #3162FF; text-decoration: underline; }
        .sponsor-info a:hover { text-decoration: underline; }
        .controls { padding: 1rem 1.5rem; border-bottom: 1px solid #e0e0e0; display: flex; gap: 1rem; flex-wrap: wrap; align-items: center; }
        .control-group { display: flex; gap: 0.5rem; align-items: center; }
        label { font-size: 0.875rem; color: #666; white-space: nowrap; }
        input, select { padding: 0.4rem 0.6rem; border: 1px solid #ddd; border-radius: 4px; font-size: 0.875rem; }
        .radio-group { display: flex; gap: 0.5rem; align-items: center; }
        .radio-group label { display: flex; align-items: center; gap: 0.3rem; cursor: pointer; font-size: 0.875rem; }
        .radio-group input[type="radio"] { margin: 0; cursor: pointer; }
        input { min-width: 150px; }
        select { min-width: 120px; }
        .feature-filter-container { display: flex; flex-wrap: wrap; align-items: center; margin: 0; padding: 0; }
        .feature-checkbox { display: inline-block; font-size: 0.8rem; white-space: nowrap; padding: 0.25rem 0.5rem; border: 1.5px solid #e0e0e0; border-radius: 16px; background: linear-gradient(to bottom, #ffffff, #f8f9fa); cursor: pointer; transition: all 0.3s ease; margin: 0; margin-right: 0.4rem; margin-bottom: 0.4rem; line-height: 1.3; color: #495057; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
        .feature-checkbox.hidden { display: none; }
        .feature-checkbox:hover { background: linear-gradient(to bottom, #f8f9fa, #e9ecef); border-color: #adb5bd; transform: translateY(-1px); box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .feature-checkbox.feature-selected { background: linear-gradient(to bottom, #e3f2fd, #bbdefb); border: 1px solid #3162FF; color: #1565c0; font-weight: 600; box-shadow: 0 2px 6px rgba(49, 98, 255, 0.2); transform: translateY(-1px); }
        .feature-checkbox.feature-selected:hover { background: linear-gradient(to bottom, #bbdefb, #90caf9); border: 1px solid #2563eb; box-shadow: 0 3px 8px rgba(49, 98, 255, 0.25); }
        .selected-features { padding: 0.3rem 1rem; border-bottom: 1px solid #e0e0e0; font-size: 0.875rem; color: #666; display: flex; flex-wrap: wrap; align-items: center; gap: 0.3rem; }
        .selected-features .model-count { flex-shrink: 0; font-weight: bold; color: #333; }
        .feature-filter-container { flex-shrink: 0; }
        .selected-features strong { color: #333; }
        .table-container { overflow-x: auto; }
        table { width: 100%; border-collapse: collapse; font-size: 0.875rem; }
        thead { background: #f8f9fa; position: sticky; top: 0; }
        th { padding: 0.75rem; text-align: left; font-weight: 600; color: #333; border-bottom: 2px solid #e0e0e0; cursor: pointer; user-select: none; }
        th:hover { background: #f0f0f0; }
        th.sort-asc::after { content: ' ▲'; font-size: 0.7rem; }
        th.sort-desc::after { content: ' ▼'; font-size: 0.7rem; }
        td { padding: 0.75rem; border-bottom: 1px solid #f0f0f0; }
        tr:hover { background: #f8f9fa; }
        .model-name { font-weight: 600; color: #3162FF; }
        .provider { color: #666; }
        .pricing { white-space: nowrap; }
        .pricing-tokens { color: #3162FF; }
        .pricing-per-use { color: #F24B42; }
        .pricing-image { color: #666; font-size: 0.8rem; }
        .features { font-size: 0.8rem; color: #666; }
        .badge { display: inline-block; padding: 0.2rem 0.4rem; margin: 0.1rem; background: #e3f2fd; color: #1976d2; border-radius: 3px; font-size: 0.75rem; }
        .loading { text-align: center; padding: 2rem; color: #666; }
        .error { color: #d32f2f; padding: 1rem; background: #ffebee; border-radius: 4px; margin: 1rem; }
        .error button { margin-top: 0.5rem; padding: 0.5rem 1rem; background: #d32f2f; color: white; border: none; border-radius: 4px; cursor: pointer; }
        .error button:hover { background: #b71c1c; }
        .count { color: #666; font-size: 0.875rem; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Agicto 模型定价</h1>
            <div class="sponsor-info">
                <div>开发者：火星人陈勇@阿尔法数聚，微信：cheny_com</div>
                <div>数据来源：<a href="https://agicto.com/model?companyId=0&typeId=0&freeType=0" target="_blank">agicto.com</a></div>
            </div>
        </div>
        <div class="controls">
            <div class="control-group">
                <span class="model-count" id="modelCount">0 个模型</span>
            </div>
            <div class="control-group">
                <label>搜索:</label>
                <input type="text" id="search" placeholder="模型名称、提供商..." oninput="filterTable()">
            </div>
            <div class="control-group">
                <label>提供商:</label>
                <select id="providerFilter" onchange="filterTable()">
                    <option value="">全部</option>
                </select>
            </div>
            <div class="control-group">
                <label>类型:</label>
                <select id="categoryFilter" onchange="updateAvailableTags()">
                    <option value="all" selected>所有</option>
                    <option value="text">文字</option>
                    <option value="multimodal">多模态+</option>
                    <option value="embedding">嵌入</option>
                    <option value="sorting">排序</option>
                </select>
            </div>
            <div class="control-group">
                <label>定价类型:</label>
                <select id="pricingTypeFilter" onchange="filterTable()">
                    <option value="">全部</option>
                    <option value="tokens">按Token</option>
                    <option value="per_use">按次计费</option>
                    <option value="image">图像</option>
                </select>
            </div>
        </div>
        <div class="selected-features" id="selectedFeatures">
            <div class="feature-filter-container" id="featureFilter"></div>
        </div>
        <div class="table-container">
            <div id="loading" class="loading">正在从 agicto.com 获取数据...</div>
            <div id="error" class="error" style="display:none;">
                <div id="errorMessage"></div>
                <button onclick="loadData()">重试</button>
            </div>
            <table id="table" style="display:none;">
                <thead>
                    <tr>
                        <th onclick="sortTable('name')">模型</th>
                        <th onclick="sortTable('provider')">提供商</th>
                        <th onclick="sortTable('context_length')">上下文长度</th>
                        <th onclick="sortTable('input_price')">输入价格</th>
                        <th onclick="sortTable('output_price')">输出价格</th>
                        <th onclick="sortTable('per_use_price')">按次计费</th>
                        <th onclick="sortTable('image_price')">图像价格</th>
                        <th onclick="sortTable('features')">功能</th>
                    </tr>
                </thead>
                <tbody id="tbody"></tbody>
            </table>
        </div>
    </div>
    <script>
        let allModels = [];
        let filteredModels = [];
        let sortColumn = '';
        let sortDirection = 'asc';
        let allFeatureTags = {}; // Store all feature tags with their category info

        async function loadData() {
            const errorEl = document.getElementById('error');
            const errorMsgEl = document.getElementById('errorMessage');
            const loadingEl = document.getElementById('loading');
            
            // Hide error, show loading
            errorEl.style.display = 'none';
            loadingEl.style.display = 'block';
            loadingEl.textContent = '正在从agicto获取数据...';
            
            let timeoutId = null;
            try {
                // Create an AbortController for timeout
                const controller = new AbortController();
                timeoutId = setTimeout(() => controller.abort(), 180000); // 3 minutes total timeout
                
                const response = await fetch('/api/models', {
                    signal: controller.signal
                });
                if (timeoutId) clearTimeout(timeoutId);
                
                if (!response.ok) {
                    throw new Error(`服务器错误: ${response.status} ${response.statusText}`);
                }
                
                const data = await response.json();
                console.log('API Response:', data); // Debug log
                
                // Check if we're using cached data
                if (data.cached) {
                    console.log('Using cached data');
                    // Show a notification that we're using cached data
                    const cachedMsg = document.createElement('div');
                    cachedMsg.id = 'cachedNotification';
                    cachedMsg.className = 'error';
                    cachedMsg.style.background = '#d1ecf1';
                    cachedMsg.style.color = '#0c5460';
                    cachedMsg.style.border = '1px solid #bee5eb';
                    cachedMsg.style.marginBottom = '1rem';
                    cachedMsg.style.padding = '0.75rem';
                    cachedMsg.innerHTML = `<div>正在使用缓存数据。后台正在更新数据，请稍后点击"刷新"获取最新数据。</div><button onclick="loadData()" style="margin-top: 0.5rem; padding: 0.5rem 1rem; background: #17a2b8; color: white; border: none; border-radius: 4px; cursor: pointer;">刷新获取最新数据</button>`;
                    const tableContainer = document.querySelector('.table-container');
                    const existingNotification = document.getElementById('cachedNotification');
                    if (existingNotification) {
                        existingNotification.remove();
                    }
                    tableContainer.insertBefore(cachedMsg, document.getElementById('table'));
                    
                    // Auto-refresh after 30 seconds to get updated data
                    setTimeout(() => {
                        console.log('Auto-refreshing to get updated data...');
                        loadData();
                    }, 30000);
                }
                
                if (data.error && !data.cached) {
                    let errorMsg = data.error;
                    if (errorMsg.includes('timed out') || errorMsg.includes('timeout')) {
                        errorMsg = '连接超时：无法从 agicto.com 获取数据。可能是网络问题或网站响应缓慢。请稍后重试。';
                    } else if (errorMsg.includes('Connection') || errorMsg.includes('connection')) {
                        errorMsg = '连接失败：无法连接到 agicto.com。请检查网络连接。';
                    }
                    errorMsgEl.textContent = errorMsg;
                    errorEl.style.display = 'block';
                    loadingEl.style.display = 'none';
                    return;
                }
                
                allModels = data.models || [];
                console.log('Loaded models count:', allModels.length); // Debug log
                
                if (allModels.length === 0) {
                    // No models found - check if there was an error in the response
                    let errorMsg = '暂无模型数据。';
                    if (data.error) {
                        errorMsg += '错误: ' + data.error;
                    } else {
                        errorMsg += '请检查控制台输出以获取详细信息。';
                    }
                    errorMsgEl.textContent = errorMsg;
                    errorEl.style.display = 'block';
                    loadingEl.style.display = 'none';
                    // Don't auto-retry - it will just keep failing
                    return;
                }
                
                setupFilters();
                filterTable();
                loadingEl.style.display = 'none';
                document.getElementById('table').style.display = 'table';
            } catch (error) {
                console.error('Load data error:', error); // Debug log
                if (timeoutId) clearTimeout(timeoutId);
                
                let errorMsg = '加载数据失败: ';
                if (error.name === 'AbortError') {
                    errorMsg = '请求超时：获取数据时间过长。请检查网络连接或稍后重试。';
                } else if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
                    errorMsg = '网络错误：无法连接到服务器。请确保 Flask 服务器正在运行。';
                } else {
                    errorMsg += error.message;
                }
                
                errorMsgEl.textContent = errorMsg;
                errorEl.style.display = 'block';
                loadingEl.style.display = 'none';
            }
        }

        function setupFilters() {
            // Setup provider filter
            const providers = [...new Set(allModels.map(m => m.provider).filter(Boolean))].sort();
            const providerSelect = document.getElementById('providerFilter');
            providers.forEach(p => {
                const option = document.createElement('option');
                option.value = p;
                option.textContent = p;
                providerSelect.appendChild(option);
            });

            // Setup feature filter (multi-select checkboxes)
            const featureFilter = document.getElementById('featureFilter');
            featureFilter.innerHTML = '';
            
            // Collect all unique features (excluding context length) and determine which models have each feature
            const allFeatures = new Set();
            allFeatureTags = {};
            
            allModels.forEach(model => {
                if (model.features) {
                    const featuresWithoutContext = model.features.filter(f => 
                        !f.startsWith('上下文长度') && f !== '逆' && f !== '支持'  // Exclude context length and error features
                    );
                    featuresWithoutContext.forEach(f => {
                        allFeatures.add(f);
                        if (!allFeatureTags[f]) {
                            allFeatureTags[f] = [];
                        }
                        allFeatureTags[f].push(model);
                    });
                }
            });
            
            const sortedFeatures = [...allFeatures].sort();
            sortedFeatures.forEach(feature => {
                const div = document.createElement('div');
                div.className = 'feature-checkbox';
                div.textContent = feature;
                div.dataset.feature = feature;
                div.onclick = function() {
                    div.classList.toggle('feature-selected');
                    filterTable();
                };
                featureFilter.appendChild(div);
            });
            
            // Initialize selected features summary and update available tags
            updateSelectedFeaturesSummary();
            updateAvailableTags();
        }

        function getModelCategory(model) {
            if (!model.features || model.features.length === 0) {
                return 'other';
            }
            const featuresWithoutContext = model.features.filter(f => !f.startsWith('上下文长度'));
            if (featuresWithoutContext.length === 0) {
                return 'other';
            }
            
            // Check if contains "支持排序" (can be with other features)
            if (featuresWithoutContext.includes('支持排序')) {
                return 'sorting';
            }
            
            // Check if only "支持文字"
            if (featuresWithoutContext.length === 1 && featuresWithoutContext[0] === '支持文本') {
                return 'text';
            }
            
            // Check if only "支持向量"
            if (featuresWithoutContext.length === 1 && featuresWithoutContext[0] === '支持向量') {
                return 'embedding';
            }
            
            // Otherwise it's multimodal+
            return 'multimodal';
        }

        function updateAvailableTags() {
            const selectedCategory = document.getElementById('categoryFilter').value;
            const featureCheckboxes = document.querySelectorAll('.feature-checkbox');
            
            featureCheckboxes.forEach(div => {
                const feature = div.dataset.feature || div.textContent;
                const modelsWithFeature = allFeatureTags[feature] || [];
                
                if (selectedCategory === 'all') {
                    // Show all tags
                    div.classList.remove('hidden');
                } else {
                    // Only show tags that exist in models of the selected category
                    const hasMatchingModel = modelsWithFeature.some(model => {
                        const modelCategory = getModelCategory(model);
                        return modelCategory === selectedCategory;
                    });
                    
                    if (hasMatchingModel) {
                        div.classList.remove('hidden');
                    } else {
                        div.classList.add('hidden');
                        // Also deselect if it was selected
                        div.classList.remove('feature-selected');
                    }
                }
            });
            
            // Re-filter table after updating tags (filterTable will be called, which also filters by category)
            filterTable();
        }

        function updateSelectedFeaturesSummary() {
            const countEl = document.getElementById('modelCount');
            const count = filteredModels.length;
            
            if (countEl) {
                countEl.textContent = `${count} 个模型`;
            }
        }

        function filterTable() {
            const search = document.getElementById('search').value.toLowerCase();
            const provider = document.getElementById('providerFilter').value;
            const pricingType = document.getElementById('pricingTypeFilter').value;
            const category = document.getElementById('categoryFilter').value;
            
            // Get selected features from divs with feature-selected class
            const selectedFeatures = [];
            document.querySelectorAll('#featureFilter .feature-checkbox.feature-selected').forEach(div => {
                selectedFeatures.push(div.dataset.feature || div.textContent);
            });

            console.log('Filtering:', { search, provider, pricingType, category, selectedFeatures, allModelsCount: allModels.length }); // Debug log

            // Update selected features summary
            updateSelectedFeaturesSummary();

            filteredModels = allModels.filter(model => {
                const matchSearch = !search || 
                    model.name.toLowerCase().includes(search) ||
                    (model.provider && model.provider.toLowerCase().includes(search)) ||
                    (model.features && model.features.some(f => f.toLowerCase().includes(search)));
                const matchProvider = !provider || model.provider === provider;
                const matchPricingType = !pricingType || (model.pricing && model.pricing.type === pricingType);
                const modelCategory = getModelCategory(model);
                const matchCategory = !category || category === 'all' || modelCategory === category;
                const matchFeatures = selectedFeatures.length === 0 || 
                    selectedFeatures.some(f => model.features && model.features.includes(f));
                
                // Debug first model
                if (allModels.indexOf(model) === 0) {
                    console.log('First model filter check:', {
                        model: model.name,
                        matchSearch,
                        matchProvider,
                        matchPricingType,
                        modelCategory,
                        matchCategory,
                        category,
                        matchFeatures,
                        selectedFeatures
                    });
                }
                
                return matchSearch && matchProvider && matchPricingType && matchCategory && matchFeatures;
            });

            console.log('Filtered models count:', filteredModels.length); // Debug log

            if (sortColumn) {
                sortTable(sortColumn, true);
            } else {
                renderTable();
            }
        }

        function sortTable(column, keepDirection = false) {
            if (!keepDirection) {
                if (sortColumn === column) {
                    sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
                } else {
                    sortColumn = column;
                    sortDirection = 'asc';
                }
            }

            filteredModels.sort((a, b) => {
                let aVal, bVal;
                if (column === 'name') {
                    aVal = a.name || '';
                    bVal = b.name || '';
                } else if (column === 'provider') {
                    aVal = a.provider || '';
                    bVal = b.provider || '';
                } else if (column === 'input_price') {
                    aVal = getInputPrice(a.pricing);
                    bVal = getInputPrice(b.pricing);
                } else if (column === 'output_price') {
                    aVal = getOutputPrice(a.pricing);
                    bVal = getOutputPrice(b.pricing);
                } else if (column === 'per_use_price') {
                    aVal = getPerUsePrice(a.pricing);
                    bVal = getPerUsePrice(b.pricing);
                } else if (column === 'image_price') {
                    aVal = getImagePrice(a.pricing);
                    bVal = getImagePrice(b.pricing);
                } else if (column === 'context_length') {
                    aVal = getContextLength(a.features);
                    bVal = getContextLength(b.features);
                } else if (column === 'features') {
                    aVal = (a.features || []).filter(f => !f.startsWith('上下文长度')).join(' ');
                    bVal = (b.features || []).filter(f => !f.startsWith('上下文长度')).join(' ');
                } else {
                    return 0;
                }

                // Handle Infinity values (no pricing/context length) - put them at the end
                if (aVal === Infinity && bVal === Infinity) return 0;
                if (aVal === Infinity) return 1;
                if (bVal === Infinity) return -1;

                const comparison = aVal < bVal ? -1 : aVal > bVal ? 1 : 0;
                return sortDirection === 'asc' ? comparison : -comparison;
            });

            // Update sort indicators
            document.querySelectorAll('th').forEach(th => {
                th.classList.remove('sort-asc', 'sort-desc');
            });
            const headers = document.querySelectorAll('th');
            headers.forEach(th => {
                if (th.getAttribute('onclick') && th.getAttribute('onclick').includes(column)) {
                    th.classList.add(sortDirection === 'asc' ? 'sort-asc' : 'sort-desc');
                }
            });

            renderTable();
        }

        function getInputPrice(pricing) {
            if (!pricing || pricing.type !== 'tokens') return Infinity;
            return pricing.input?.price || Infinity;
        }

        function getOutputPrice(pricing) {
            if (!pricing || pricing.type !== 'tokens') return Infinity;
            return pricing.output?.price || Infinity;
        }

        function getPerUsePrice(pricing) {
            if (!pricing || pricing.type !== 'per_use') return Infinity;
            return pricing.price || Infinity;
        }

        function getImagePrice(pricing) {
            if (!pricing || pricing.type !== 'image') return Infinity;
            if (pricing.tiers && pricing.tiers.length > 0) {
                const minPrice = Math.min(...pricing.tiers.map(t => t.price || Infinity));
                return minPrice !== Infinity ? minPrice : Infinity;
            }
            return Infinity;
        }

        function getContextLength(features) {
            if (!features) return Infinity;
            const contextFeature = features.find(f => f.startsWith('上下文长度'));
            if (!contextFeature) return Infinity;
            
            // Extract number from "上下文长度: 400K" or "上下文长度: 200K"
            const match = contextFeature.match(/上下文长度:\s*(\d+)([KM]?)/i);
            if (!match) return Infinity;
            
            let value = parseFloat(match[1]);
            const unit = match[2].toUpperCase();
            
            // Convert to tokens for comparison (K = 1000, M = 1000000)
            if (unit === 'K') {
                value = value * 1000;
            } else if (unit === 'M') {
                value = value * 1000000;
            }
            
            return value;
        }

        function formatContextLength(features) {
            if (!features) return '-';
            const contextFeature = features.find(f => f.startsWith('上下文长度'));
            return contextFeature ? contextFeature.replace('上下文长度:', '').trim() : '-';
        }

        function formatInputPrice(pricing) {
            if (!pricing || pricing.type !== 'tokens') return '-';
            return pricing.input ? `￥${pricing.input.price}/${pricing.input.unit}` : '-';
        }

        function formatOutputPrice(pricing) {
            if (!pricing || pricing.type !== 'tokens') return '-';
            return pricing.output ? `￥${pricing.output.price}/${pricing.output.unit}` : '-';
        }

        function formatPerUsePrice(pricing) {
            if (!pricing || pricing.type !== 'per_use') return '-';
            return `￥${pricing.price}/${pricing.unit}`;
        }

        function formatImagePrice(pricing) {
            if (!pricing || pricing.type !== 'image') return '-';
            if (pricing.tiers && pricing.tiers.length > 0) {
                const minTier = pricing.tiers.reduce((min, t) => (t.price < min.price ? t : min), pricing.tiers[0]);
                return `￥${minTier.price}/${minTier.unit} (${pricing.tiers.length} tiers)`;
            }
            return '-';
        }

        function renderTable() {
            const tbody = document.getElementById('tbody');
            tbody.innerHTML = '';

            filteredModels.forEach(model => {
                const row = document.createElement('tr');
                // Filter out context length from features display since it's now a separate column
                const displayFeatures = (model.features || []).filter(f => !f.startsWith('上下文长度'));
                
                row.innerHTML = `
                    <td><span class="model-name">${escapeHtml(model.name)}</span></td>
                    <td><span class="provider">${escapeHtml(model.provider || '-')}</span></td>
                    <td><span class="pricing">${escapeHtml(formatContextLength(model.features))}</span></td>
                    <td><span class="pricing pricing-tokens">${escapeHtml(formatInputPrice(model.pricing))}</span></td>
                    <td><span class="pricing pricing-tokens">${escapeHtml(formatOutputPrice(model.pricing))}</span></td>
                    <td><span class="pricing pricing-per-use">${escapeHtml(formatPerUsePrice(model.pricing))}</span></td>
                    <td><span class="pricing pricing-image">${escapeHtml(formatImagePrice(model.pricing))}</span></td>
                    <td><span class="features">${displayFeatures.map(f => `<span class="badge">${escapeHtml(f)}</span>`).join('') || '-'}</span></td>
                `;
                tbody.appendChild(row);
            });

            // Update the summary line with count and selected features
            updateSelectedFeaturesSummary();
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        // Initialize on page load
        loadData();
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    """Serve the main page."""
    return render_template_string(HTML_TEMPLATE)


def get_json_path():
    """Get the path to the JSON cache file."""
    script_dir = Path(__file__).parent
    return script_dir / "agicto_models.json"


def load_models_from_json():
    """Load models from JSON cache file if it exists."""
    json_path = get_json_path()
    if json_path.exists():
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                models = data.get('models', [])
                print(f"Loaded {len(models)} models from cache: {json_path}")
                return models
        except Exception as e:
            print(f"Error loading cache: {e}")
    return None


def save_models_to_json(models):
    """Save models to JSON cache file."""
    json_path = get_json_path()
    try:
        output = {"models": models}
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(models)} models to cache: {json_path}")
    except Exception as e:
        print(f"Error saving cache: {e}")


@app.route('/api/models')
def get_models():
    """Fetch models from agicto.com and return as JSON. Loads from cache first, then fetches new data."""
    
    # First, try to load from cache
    cached_models = load_models_from_json()
    
    # Return cached data immediately if available
    if cached_models:
        print(f"Returning cached data immediately ({len(cached_models)} models)")
        # Start fetching new data in background
        def fetch_and_save():
            try:
                url = "https://agicto.com/model?companyId=0&typeId=0&freeType=0"
                print(f"Background: Fetching models from {url}...")
                html_content = fetch_page(url)
                print(f"Background: Fetched {len(html_content)} characters of HTML")
                models = extract_all_models(html_content)
                print(f"Background: Extracted {len(models)} models")
                save_models_to_json(models)
                print(f"Background: Saved {len(models)} models to cache")
            except Exception as e:
                import traceback
                print(f"Background fetch failed (this is okay, cache is backup): {e}")
                print(f"Traceback: {traceback.format_exc()}")
        
        # Start background thread
        thread = threading.Thread(target=fetch_and_save, daemon=True)
        thread.start()
        
        return jsonify({"models": cached_models, "cached": True})
    
    # No cache available, try to fetch new data (blocking)
    # This is the normal flow - cache is just a backup
    try:
        url = "https://agicto.com/model?companyId=0&typeId=0&freeType=0"
        print(f"Fetching models from {url}...")
        html_content = fetch_page(url)
        print(f"Fetched {len(html_content)} characters of HTML")
        models = extract_all_models(html_content)
        print(f"Extracted {len(models)} models")
        
        if len(models) == 0:
            # Check if HTML was fetched but no models found
            if 'ant-col' in html_content or '/model/' in html_content:
                error_msg = "页面已加载但未找到模型数据。可能原因：1) 网站结构变化 2) 解析逻辑需要更新"
            else:
                error_msg = "页面内容未正确加载。HTML中未找到模型相关元素。"
            print(f"ERROR: {error_msg}")
            print(f"HTML长度: {len(html_content)} 字符")
            return jsonify({
                "models": [],
                "error": error_msg
            })
        
        # Save new data to JSON
        save_models_to_json(models)
        
        return jsonify({"models": models})
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Fetch failed: {e}")
        print(f"Traceback: {error_trace}")
        # Return error information to help debug
        return jsonify({
            "models": [],
            "error": f"获取数据失败: {str(e)}"
        })


if __name__ == '__main__':
    import sys
    import webbrowser
    import time
    
    # Check command line arguments
    debug_mode = '--debug' in sys.argv
    no_browser = '--no-browser' in sys.argv
    
    def open_browser():
        """Wait for server to start, then open browser."""
        time.sleep(1.5)  # Wait for server to start
        url = "http://localhost:5000"
        print(f"正在打开浏览器: {url}")
        webbrowser.open(url)
    
    print("正在启动 Agicto 定价 Web 界面...")
    
    # Only auto-open browser if --no-browser flag is not set
    # This allows batch files to control when to open the browser
    if not no_browser:
        print("浏览器将自动打开 http://localhost:5000")
        # Start browser in a separate thread
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
    else:
        print("请在浏览器中打开 http://localhost:5000")
    
    app.run(debug=debug_mode, host='127.0.0.1', port=5000)



