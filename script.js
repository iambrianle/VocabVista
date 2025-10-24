document.getElementById('analyze-btn').addEventListener('click', () => {
    const text = document.getElementById('text-input').value;
    const analyzeBtn = document.getElementById('analyze-btn');
    const heatmapOutput = document.getElementById('heatmap-output');
    
    // Show processing indicator
    analyzeBtn.disabled = true;
    analyzeBtn.textContent = 'Processing...';
    heatmapOutput.innerHTML = '<div class="processing-indicator">Analyzing text... This may take a moment for large texts.</div>';
    
    fetch('http://127.0.0.1:5000/analyze', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ text })
    })
    .then(response => response.json())
    .then(data => {
        heatmapOutput.innerHTML = '';
        
        // Sort tokens by their position in the original text
        data.sort((a, b) => a.position - b.position);
        
        data.forEach(item => {
            const span = document.createElement('span');
            span.textContent = item.token;
            
            if (item.color) {
                // For words, apply the heatmap color
                span.style.backgroundColor = item.color;
                span.style.padding = '2px 4px';
                span.style.margin = '0 1px';
                // Add tooltip to show frequency and rarity classification
                span.title = `Frequency: ${item.frequency} (per million) - ${getRarityLabel(item.frequency)}`;
            } else {
                // For non-word tokens (spaces, punctuation), don't apply color
                span.style.backgroundColor = 'transparent';
            }
            
            heatmapOutput.appendChild(span);
        });
    })
    .catch(error => {
        console.error('Error:', error);
        heatmapOutput.innerHTML = '<div class="error-message">Error analyzing text. Please try again.</div>';
    })
    .finally(() => {
        // Reset button state
        analyzeBtn.disabled = false;
        analyzeBtn.textContent = 'Analyze';
    });
});

// Function to determine word rarity classification
function getRarityLabel(frequency) {
    if (frequency <= 0.1) {
        return 'Very Rare';
    } else if (frequency <= 1) {
        return 'Rare';
    } else if (frequency <= 10) {
        return 'Uncommon';
    } else if (frequency <= 100) {
        return 'Common';
    } else {
        return 'Very Common';
    }
}
