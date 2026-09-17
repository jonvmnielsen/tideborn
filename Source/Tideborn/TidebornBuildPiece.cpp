#include "TidebornBuildPiece.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "UObject/ConstructorHelpers.h"

ATidebornBuildPiece::ATidebornBuildPiece()
{
	PrimaryActorTick.bCanEverTick = false;

	Mesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Mesh"));
	SetRootComponent(Mesh);
	Mesh->SetMobility(EComponentMobility::Movable);
	Mesh->SetCollisionProfileName(TEXT("BlockAll"));

	static ConstructorHelpers::FObjectFinder<UStaticMesh> FoundMesh(TEXT("/Game/Tideborn/Meshes/SM_Foundation.SM_Foundation"));
	if (FoundMesh.Succeeded())
	{
		Mesh->SetStaticMesh(FoundMesh.Object);
		Mesh->SetRelativeScale3D(FVector(1.f));
	}
	else
	{
		static ConstructorHelpers::FObjectFinder<UStaticMesh> CubeMesh(TEXT("/Engine/BasicShapes/Cube.Cube"));
		if (CubeMesh.Succeeded())
		{
			Mesh->SetStaticMesh(CubeMesh.Object);
			Mesh->SetRelativeScale3D(FVector(2.0f, 2.0f, 0.25f));
		}
	}
}

void ATidebornBuildPiece::ConfigureAsGhost()
{
	if (!Mesh)
	{
		return;
	}
	Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	SetActorEnableCollision(false);
	if (UMaterialInterface* Base = LoadObject<UMaterialInterface>(nullptr, TEXT("/Engine/BasicShapes/BasicShapeMaterial")))
	{
		if (UMaterialInstanceDynamic* Dyn = UMaterialInstanceDynamic::Create(Base, this))
		{
			Dyn->SetVectorParameterValue(TEXT("Color"), FLinearColor(0.2f, 0.8f, 1.f, 0.35f));
			Mesh->SetMaterial(0, Dyn);
		}
	}
}

void ATidebornBuildPiece::ConfigureAsPlaced()
{
	if (!Mesh)
	{
		return;
	}
	Mesh->SetCollisionProfileName(TEXT("BlockAll"));
	SetActorEnableCollision(true);
	// Keep imported wood materials when available
	if (UMaterialInterface* Plank = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Tideborn/Meshes/M_Plank.M_Plank")))
	{
		Mesh->SetMaterial(0, Plank);
	}
}
