document.getElementById('analyze-btn').addEventListener('click', () => {
    const text = document.getElementById('text-input').value;
    const analyzeBtn = document.getElementById('analyze-btn');
    const heatmapOutput = document.getElementById('heatmap-output');
    
    // Show processing indicator
    analyzeBtn.disabled = true;
    analyzeBtn.textContent = 'Processing...';
    heatmapOutput.innerHTML = '<div class="processing-indicator">Analyzing text... This may take a moment for large texts.</div>';
    
    const baseUrl = window.location.origin;
    fetch(`${baseUrl}/analyze`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ text })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('API Response:', data); // Debug log
        heatmapOutput.innerHTML = '';
        
        // Sort tokens by their position in the original text
        data.sort((a, b) => a.position - b.position);
        
        data.forEach(item => {
            const span = document.createElement('span');
            span.textContent = item.token;
            
            if (item.color) {
                // For words, apply the heatmap color
                span.style.backgroundColor = item.color;
                span.style.padding = '3px 6px';
                span.style.margin = '0 1px';
                span.style.borderRadius = '4px';
                // Add tooltip to show frequency and rarity classification
                span.title = `Frequency: ${item.frequency.toFixed(2)} (per million) - ${item.rarity}`;
            } else {
                // For non-word tokens (spaces, punctuation), don't apply color
                span.style.backgroundColor = 'transparent';
            }
            
            heatmapOutput.appendChild(span);
        });
        
        if (data.length === 0) {
            heatmapOutput.innerHTML = '<div class="error-message">No text to analyze. Please enter some text.</div>';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        console.error('Error details:', error.message, error.stack);
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
