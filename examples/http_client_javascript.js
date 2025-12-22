/**
 * JavaScript/Node.js client examples for LightRAG MCP HTTP Server.
 *
 * Install dependencies:
 *   npm install axios
 */

const axios = require('axios');

class LightRAGHTTPClient {
  /**
   * Initialize the client.
   * @param {string} baseUrl - Base URL of the HTTP server
   * @param {string} prefix - Tool prefix to use
   */
  constructor(baseUrl = 'http://localhost:8000', prefix = 'default') {
    this.baseUrl = baseUrl.replace(/\/$/, '');
    this.prefix = prefix;
    this.client = axios.create({
      baseURL: this.baseUrl,
      headers: {
        'Content-Type': 'application/json'
      }
    });
  }

  /**
   * Get full URL for a tool.
   */
  _toolUrl(toolName) {
    if (!toolName.startsWith(`${this.prefix}_`)) {
      toolName = `${this.prefix}_${toolName}`;
    }
    return `/mcp/${this.prefix}/${toolName}`;
  }

  /**
   * Check server health.
   */
  async health() {
    const response = await this.client.get('/health');
    return response.data;
  }

  /**
   * List all tools for this prefix.
   */
  async listTools() {
    const response = await this.client.get(`/mcp/${this.prefix}/tools`);
    return response.data;
  }

  /**
   * Execute a tool and return the result.
   * @param {string} toolName - Tool name (without or with prefix)
   * @param {object} arguments - Tool arguments
   */
  async executeTool(toolName, arguments = {}) {
    const url = this._toolUrl(toolName);
    const response = await this.client.post(url, { arguments });
    return response.data;
  }

  /**
   * Execute a tool with streaming response.
   * @param {string} toolName - Tool name
   * @param {object} arguments - Tool arguments
   * @param {function} onChunk - Callback for each chunk
   */
  async executeToolStream(toolName, arguments = {}, onChunk) {
    const url = this._toolUrl(toolName);
    const response = await this.client.post(
      url,
      { arguments, stream: true },
      { responseType: 'stream' }
    );

    return new Promise((resolve, reject) => {
      let buffer = '';

      response.data.on('data', (chunk) => {
        buffer += chunk.toString();
        const lines = buffer.split('\n');
        buffer = lines.pop(); // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.trim()) {
            try {
              const data = JSON.parse(line);
              if (data.type === 'chunk') {
                onChunk(data.data);
              } else if (data.type === 'done') {
                resolve(data);
              } else if (data.type === 'error') {
                reject(new Error(data.error));
              }
            } catch (e) {
              console.error('Failed to parse JSON:', line);
            }
          }
        }
      });

      response.data.on('end', () => {
        resolve();
      });

      response.data.on('error', (error) => {
        reject(error);
      });
    });
  }

  // Convenient methods for common tools

  async queryText(query, mode = 'hybrid') {
    const result = await this.executeTool('query_text', { query, mode });
    return result.data.response;
  }

  async queryTextStream(query, mode = 'hybrid', onChunk) {
    return this.executeToolStream('query_text_stream', { query, mode }, onChunk);
  }

  async insertText(text) {
    const result = await this.executeTool('insert_text', { text });
    return result.data;
  }

  async insertTexts(texts) {
    const result = await this.executeTool('insert_texts', { texts });
    return result.data;
  }

  async getDocuments(page = 1, pageSize = 20) {
    const result = await this.executeTool('get_documents_paginated', {
      page,
      page_size: pageSize
    });
    return result.data;
  }

  async getKnowledgeGraph() {
    const result = await this.executeTool('get_knowledge_graph', {});
    return result.data;
  }
}

// Example 1: Basic Usage
async function exampleBasicUsage() {
  console.log('='.repeat(70));
  console.log('Example 1: Basic Usage');
  console.log('='.repeat(70));

  const client = new LightRAGHTTPClient('http://localhost:8000', 'novel_style');

  // Health check
  const health = await client.health();
  console.log(`Server status: ${health.status}`);
  console.log(`Available prefixes: ${health.prefixes.join(', ')}\n`);

  // List tools
  const toolsInfo = await client.listTools();
  console.log(`Tools for prefix '${client.prefix}': ${toolsInfo.count}`);
  console.log(`First tool: ${toolsInfo.tools[0].name}\n`);

  // Query
  const response = await client.queryText('What writing techniques are used?');
  console.log(`Query response: ${response.substring(0, 100)}...\n`);
}

// Example 2: Streaming Query
async function exampleStreaming() {
  console.log('='.repeat(70));
  console.log('Example 2: Streaming Query');
  console.log('='.repeat(70));

  const client = new LightRAGHTTPClient('http://localhost:8000', 'novel_content');

  process.stdout.write('Streaming query: ');

  await client.queryTextStream(
    'Summarize the main plot',
    'hybrid',
    (chunk) => {
      process.stdout.write(chunk);
    }
  );

  console.log('\n');
}

// Example 3: Document Management
async function exampleDocumentManagement() {
  console.log('='.repeat(70));
  console.log('Example 3: Document Management');
  console.log('='.repeat(70));

  const client = new LightRAGHTTPClient('http://localhost:8000', 'novel_content');

  // Insert single document
  const result = await client.insertText(
    'Chapter 20: The final confrontation begins...'
  );
  console.log(`Inserted document, track_id: ${result.track_id || 'N/A'}`);

  // Insert multiple documents
  const docs = [
    {
      title: 'Chapter 21',
      content: 'The hero faces their greatest challenge...',
      metadata: { chapter: 21 }
    },
    {
      title: 'Chapter 22',
      content: 'Victory comes at a great cost...',
      metadata: { chapter: 22 }
    }
  ];
  await client.insertTexts(docs);
  console.log(`Inserted ${docs.length} documents`);

  // Get documents
  const docsPage = await client.getDocuments(1, 10);
  console.log(`Total documents: ${docsPage.total || 'N/A'}`);
  console.log(`Current page: ${docsPage.page || 'N/A'}\n`);
}

// Example 4: Knowledge Graph
async function exampleKnowledgeGraph() {
  console.log('='.repeat(70));
  console.log('Example 4: Knowledge Graph');
  console.log('='.repeat(70));

  const client = new LightRAGHTTPClient('http://localhost:8000', 'novel_style');

  // Get knowledge graph
  const graph = await client.getKnowledgeGraph();
  const nodes = graph.nodes || [];
  const edges = graph.edges || [];

  console.log('Knowledge graph:');
  console.log(`  Nodes: ${nodes.length}`);
  console.log(`  Edges: ${edges.length}`);

  if (nodes.length > 0) {
    console.log(`\nFirst node:`, nodes[0]);
  }

  if (edges.length > 0) {
    console.log(`First edge:`, edges[0]);
  }

  console.log();
}

// Example 5: Error Handling
async function exampleErrorHandling() {
  console.log('='.repeat(70));
  console.log('Example 5: Error Handling');
  console.log('='.repeat(70));

  const client = new LightRAGHTTPClient('http://localhost:8000', 'novel_style');

  try {
    // This will fail - wrong tool name
    await client.executeTool('nonexistent_tool', {});
  } catch (error) {
    if (error.response) {
      console.log(`HTTP Error: ${error.response.status}`);
      console.log(`Response:`, error.response.data);
    } else {
      console.log(`Error: ${error.message}`);
    }
  }

  console.log();
}

// Example 6: Raw API Calls
async function exampleRawAPICalls() {
  console.log('='.repeat(70));
  console.log('Example 6: Raw API Calls');
  console.log('='.repeat(70));

  const baseUrl = 'http://localhost:8000';
  const prefix = 'novel_style';

  // Health check
  const healthResponse = await axios.get(`${baseUrl}/health`);
  console.log('Health:', healthResponse.data);

  // Execute tool directly
  const response = await axios.post(
    `${baseUrl}/mcp/${prefix}/${prefix}_query_text`,
    {
      arguments: {
        query: "What is the author's style?",
        mode: 'hybrid'
      }
    }
  );

  console.log(`Success: ${response.data.success}`);
  console.log(`Response length: ${response.data.data.response.length} chars\n`);
}

// Main execution
async function main() {
  console.log('\n' + '='.repeat(70));
  console.log('LightRAG MCP HTTP Client Examples (Node.js)');
  console.log('='.repeat(70) + '\n');

  console.log('Note: Make sure the HTTP server is running:');
  console.log('  daniel-lightrag-http\n');

  try {
    await exampleBasicUsage();
    // await exampleStreaming();  // Uncomment if streaming endpoint is available
    // await exampleDocumentManagement();  // Uncomment to test
    // await exampleKnowledgeGraph();  // Uncomment to test
    await exampleErrorHandling();
    await exampleRawAPICalls();

    console.log('='.repeat(70));
    console.log('All examples completed!');
    console.log('='.repeat(70));
  } catch (error) {
    if (error.code === 'ECONNREFUSED') {
      console.log('\nError: Could not connect to HTTP server');
      console.log('Please start the server with: daniel-lightrag-http');
    } else {
      console.log(`\nError: ${error.message}`);
      console.log(error);
    }
  }
}

// Export for use as module
module.exports = { LightRAGHTTPClient };

// Run if executed directly
if (require.main === module) {
  main().catch(console.error);
}
