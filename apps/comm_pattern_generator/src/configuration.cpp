#include "configuration.hpp"

// STL
#include <vector>
#include <string>
#include <fstream>
#include <iostream>

// Used to parse the configuration file 
#include "external/nlohmann/json.hpp"

// Used to broadcast the configuration so that only one MPI process needs to 
// read it in from file
#include "boost/mpi.hpp"
#include "boost/archive/text_oarchive.hpp"
#include "boost/archive/text_iarchive.hpp"

// Internal
#include "comm_pattern.hpp"

Configuration::Configuration( const std::string config_file_path ) 
{
  std::ifstream config_stream( config_file_path );
  nlohmann::json config_json = nlohmann::json::parse( config_stream );
  nlohmann::json comm_patterns = config_json["comm_patterns"];
  for ( auto elem : comm_patterns ) {
    auto pattern_name = elem["pattern_name"];
    auto n_iters = elem["n_iters"];
    auto nd_fraction = elem["nd_fraction"];
    nlohmann::json params_json = elem["params"];
    std::unordered_map<std::string,int> params;
    for ( auto p : params_json ) {
      std::string key = p["key"];
      int val = p["val"];
      params.insert( { key, val } );
    }
    CommPattern comm_pattern( pattern_name, n_iters, nd_fraction, params );
    comm_pattern_seq.push_back( comm_pattern );
  }
}

void Configuration::print() const 
{
  for ( auto comm_pattern : comm_pattern_seq ) {
    std::cout << "Comm. Pattern: " << comm_pattern.pattern_name << ", "
              << "# Iterations: " << comm_pattern.n_iters << ", "
              << "% Non-Deterministic " << comm_pattern.nd_fraction 
              << std::endl;
    std::cout << "Parameters: " << std::endl;
    for ( auto kvp : comm_pattern.params ) {
      std::cout << "\t" << kvp.first << " --> " << kvp.second << std::endl;
    }
    std::cout << std::endl;
  }
}

void broadcast_config( Configuration& config ) 
{
  boost::mpi::communicator world;
  int rank = world.rank();
  std::stringstream config_ss;
  boost::archive::text_oarchive config_oarchive { config_ss };
  if ( rank == 0 ) {
    config_oarchive << config;
  }
  std::string config_payload = config_ss.str();
  boost::mpi::broadcast( world, config_payload, 0 );
  if ( rank != 0 ) {
    std::istringstream config_iss( config_payload );
    boost::archive::text_iarchive config_iarchive { config_iss };
    config_iarchive >> config;
  }
}

////////////////////////////////////////////////////////////////////////////////
/////////////////////// Needed for ingest-broadcast idiom //////////////////////
////////////////////////////////////////////////////////////////////////////////

Configuration::Configuration() 
{
}

Configuration& Configuration::operator=( const Configuration& rhs )
{
  if ( &rhs == this ) {
    return *this;
  }
  this->comm_pattern_seq = rhs.get_comm_pattern_seq();
  return *this;
}

std::vector<CommPattern> Configuration::get_comm_pattern_seq() const 
{
  return this->comm_pattern_seq;
}
